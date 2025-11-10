# Quick Start Guide - Workflow Loops

## Setup (One-time)

1. **Start Temporal Server**:
   ```bash
   temporal server start-dev
   ```

2. **Open Temporal UI** (in browser):
   ```
   http://localhost:8233
   ```

3. **Navigate to examples**:
   ```bash
   cd MY/0_simple/workflow_loop
   ```

## Run Examples (in order)

### 1. Simple Loop (5 minutes)
```bash
python simple_loop.py
```

**What you'll see**: Basic loop concept - activities A → B → C, loops back to A if condition not met.

**Expected loops**: ~3 iterations until score reaches 80+

---

### 2. Loop with Retry (5 minutes)
```bash
python loop_with_retry.py
```

**What you'll see**: Document processing that loops back for quality improvements.

**Expected loops**: 1-2 iterations per test case

---

### 3. Complex Multi-Loop (10 minutes) ⭐ **RECOMMENDED**
```bash
python complex_multi_loop.py
```

**What you'll see**:
- **LOOP 1**: Order validation (customer, inventory, payment)
- **LOOP 2**: Fulfillment with **nested** packaging quality loop
- **LOOP 3**: Delivery attempts

**Expected output**: Multiple phases with detailed logging showing all loop iterations

## View in Temporal UI

After running any example:

1. Go to http://localhost:8233
2. Click on the workflow execution
3. See the **Event History** showing:
   - All activity executions
   - How many times each activity ran
   - Loop iterations clearly visible

## Files in This Folder

| File | Description |
|------|-------------|
| `simple_loop.py` | Basic loop concept (start here) |
| `loop_with_retry.py` | Document processing with quality loop |
| `complex_multi_loop.py` | **Production-grade** multi-loop example ⭐ |
| `workflow_diagram.md` | **Mermaid diagrams** visualizing workflows |
| `README.md` | Complete guide with patterns and concepts |
| `COMPLEX_WORKFLOW_README.md` | Detailed docs for complex example |
| `QUICKSTART.md` | This file |

## Understanding the Diagrams

Open `workflow_diagram.md` in:
- **VS Code**: Install "Markdown Preview Mermaid Support" extension
- **GitHub**: Diagrams auto-render
- **Online**: Copy to https://mermaid.live

## Key Concepts

### What is a LOOP?
A workflow goes through activities A → B → C, and if condition in C fails, it **loops back** to A or B (revisiting already-executed activities).

### Why Use Loops?
- **Retry with corrections**: Process → Check → Re-process with feedback
- **Quality gates**: Keep improving until threshold met
- **Approval workflows**: Submit → Review → Revise → Resubmit
- **Delivery retries**: Attempt → Fail → Retry

### Best Practices
1. ✅ Always set `max_attempts` (prevent infinite loops)
2. ✅ Log each iteration clearly
3. ✅ Update state before looping back
4. ✅ Handle max attempts gracefully

## Next Steps

1. Run all three examples to see different loop patterns
2. View workflows in Temporal UI to see event history
3. Read `workflow_diagram.md` to visualize the flow
4. Modify examples to experiment with:
   - Different max attempts
   - Different thresholds
   - Additional activities in loops
5. Read `COMPLEX_WORKFLOW_README.md` for production tips

## Troubleshooting

**Temporal server not running?**
```bash
temporal server start-dev
```

**Port 8233 already in use?**
- Check if another Temporal instance is running
- Or use the existing one

**Want to see more details?**
- Check console output for detailed logs
- View workflow in Temporal UI for event timeline

## Questions?

- Read `README.md` for detailed concepts
- See `workflow_diagram.md` for visual flow
- Check `COMPLEX_WORKFLOW_README.md` for advanced topics
