"""REST API for interacting with order processing workflows."""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from temporalio.client import Client

from models import (
    OrderDetails,
    OrderItem,
    OrderState,
    PaymentInfo,
    ShippingInfo,
)
from workflows import OrderProcessingWorkflow

app = FastAPI(title="E-commerce Order Processing API")

# Global client (initialized on startup)
temporal_client: Optional[Client] = None


class CreateOrderRequest(BaseModel):
    """Request to create a new order."""
    customer_id: str
    items: list[dict]
    shipping_address: str
    shipping_city: str
    shipping_postal_code: str
    shipping_country: str


class ConfirmPaymentRequest(BaseModel):
    """Request to confirm payment."""
    transaction_id: str
    amount: float
    payment_method: str


class CancelOrderRequest(BaseModel):
    """Request to cancel an order."""
    reason: str


@app.on_event("startup")
async def startup():
    """Initialize Temporal client on startup."""
    global temporal_client
    temporal_client = await Client.connect("localhost:7233")
    print("✅ Connected to Temporal server")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    if temporal_client:
        await temporal_client.close()


@app.post("/orders", status_code=201)
async def create_order(request: CreateOrderRequest):
    """
    Create a new order and start the workflow.

    This initiates the order processing workflow in Temporal.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    # Generate order ID
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Parse items
    items = [
        OrderItem(
            product_id=item["product_id"],
            product_name=item["product_name"],
            quantity=item["quantity"],
            price=item["price"]
        )
        for item in request.items
    ]

    # Calculate total
    total_amount = sum(item.price * item.quantity for item in items)

    # Create order details
    order_details = OrderDetails(
        order_id=order_id,
        customer_id=request.customer_id,
        items=items,
        total_amount=total_amount,
        shipping_info=ShippingInfo(
            address=request.shipping_address,
            city=request.shipping_city,
            postal_code=request.shipping_postal_code,
            country=request.shipping_country,
        )
    )

    # Start workflow
    handle = await temporal_client.start_workflow(
        OrderProcessingWorkflow.run,
        order_details,
        id=f"order-{order_id}",
        task_queue="order-processing-queue",
    )

    return {
        "order_id": order_id,
        "workflow_id": handle.id,
        "status": "pending",
        "total_amount": total_amount,
        "message": "Order created successfully. Awaiting payment confirmation."
    }


@app.post("/orders/{order_id}/payment")
async def confirm_payment(order_id: str, request: ConfirmPaymentRequest):
    """
    Send payment confirmation signal to the workflow.

    This demonstrates the SIGNAL pattern - external system (payment gateway)
    sends data to update the workflow state.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"order-{order_id}"

    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Send signal
        payment_info = PaymentInfo(
            transaction_id=request.transaction_id,
            amount=request.amount,
            payment_method=request.payment_method,
            timestamp=datetime.now()
        )

        await handle.signal(OrderProcessingWorkflow.confirm_payment, payment_info)

        return {
            "order_id": order_id,
            "message": "Payment confirmation sent successfully",
            "transaction_id": request.transaction_id
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Order not found: {str(e)}")


@app.delete("/orders/{order_id}")
async def cancel_order(order_id: str, request: CancelOrderRequest):
    """
    Send cancellation signal to the workflow.

    This demonstrates the SIGNAL pattern for triggering workflow actions.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"order-{order_id}"

    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Send cancellation signal
        await handle.signal(OrderProcessingWorkflow.cancel_order, request.reason)

        return {
            "order_id": order_id,
            "message": "Order cancellation initiated",
            "reason": request.reason
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Order not found: {str(e)}")


@app.get("/orders/{order_id}/status")
async def get_order_status(order_id: str):
    """
    Query the current order status.

    This demonstrates the QUERY pattern - read-only access to workflow state.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"order-{order_id}"

    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Query status (read-only, no side effects)
        status = await handle.query(OrderProcessingWorkflow.get_order_status)

        return {
            "order_id": order_id,
            "status": status
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Order not found: {str(e)}")


@app.get("/orders/{order_id}")
async def get_order_details(order_id: str):
    """
    Query the complete order state.

    This demonstrates the QUERY pattern - retrieving complex state data.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"order-{order_id}"

    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Query full state
        state: OrderState = await handle.query(OrderProcessingWorkflow.get_full_state)

        return {
            "order_id": state.order_id,
            "customer_id": state.customer_id,
            "status": state.status.value,
            "total_amount": state.total_amount,
            "payment_info": {
                "transaction_id": state.payment_info.transaction_id,
                "amount": state.payment_info.amount,
                "payment_method": state.payment_info.payment_method,
                "timestamp": state.payment_info.timestamp.isoformat()
            } if state.payment_info else None,
            "shipment_info": {
                "tracking_number": state.shipment_info.tracking_number,
                "provider": state.shipment_info.provider.value,
                "estimated_delivery": state.shipment_info.estimated_delivery.isoformat(),
                "shipped_at": state.shipment_info.shipped_at.isoformat()
            } if state.shipment_info else None,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
            "estimated_delivery": state.estimated_delivery.isoformat() if state.estimated_delivery else None,
            "cancellation_reason": state.cancellation_reason
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Order not found: {str(e)}")


@app.get("/orders/{order_id}/delivery")
async def get_estimated_delivery(order_id: str):
    """
    Query the estimated delivery date.

    This demonstrates the QUERY pattern - accessing specific state fields.
    """
    if not temporal_client:
        raise HTTPException(status_code=500, detail="Temporal client not initialized")

    workflow_id = f"order-{order_id}"

    try:
        # Get workflow handle
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Query estimated delivery
        estimated_delivery = await handle.query(
            OrderProcessingWorkflow.get_estimated_delivery
        )

        if estimated_delivery:
            return {
                "order_id": order_id,
                "estimated_delivery": estimated_delivery.isoformat()
            }
        else:
            return {
                "order_id": order_id,
                "estimated_delivery": None,
                "message": "Order not yet shipped"
            }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Order not found: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "temporal_connected": temporal_client is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
