import {
  Badge,
  Button,
  Card,
  CardHeader,
  Dropdown,
  Input,
  makeStyles,
  Option,
  shorthands,
  Spinner,
  Text,
  Textarea,
  tokens,
} from "@fluentui/react-components";
import {
  BrainCircuit24Regular,
  CheckmarkCircle24Regular,
  Clock24Regular,
  Code24Regular,
  Delete24Regular,
  Document24Regular,
  Send24Regular,
} from "@fluentui/react-icons";
import axios from "axios";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const useStyles = makeStyles({
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    backgroundColor: tokens.colorNeutralBackground2,
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    ...shorthands.padding("20px"),
    backgroundColor: tokens.colorBrandBackground,
    color: tokens.colorNeutralForegroundOnBrand,
    flexShrink: 0,
  },
  headerTitle: {
    display: "flex",
    flexDirection: "column",
  },
  main: {
    display: "flex",
    flexDirection: "column",
    flexGrow: 1,
    ...shorthands.padding("20px"),
    minHeight: 0, // Critical for flex overflow
  },
  chatContainer: {
    display: "flex",
    flexDirection: "column",
    flexGrow: 1,
    ...shorthands.gap("16px"),
    overflowY: "auto",
    overflowX: "hidden",
    ...shorthands.padding("10px"),
    marginBottom: "20px",
    minHeight: 0, // Critical for flex overflow
  },
  userMessage: {
    maxWidth: "70%",
    ...shorthands.padding("12px", "16px"),
    alignSelf: "flex-end",
    backgroundColor: tokens.colorBrandBackground2,
    flexShrink: 0,
  },
  systemMessage: {
    maxWidth: "70%",
    ...shorthands.padding("12px", "16px"),
    alignSelf: "flex-start",
    backgroundColor: tokens.colorNeutralBackground1,
    flexShrink: 0,
  },
  inputContainer: {
    display: "flex",
    ...shorthands.gap("12px"),
    alignItems: "flex-end",
    flexShrink: 0,
  },
  workflowSelector: {
    minWidth: "200px",
  },
  messageInput: {
    flexGrow: 1,
  },
  activityBadge: {
    marginTop: "8px",
  },
  markdownContent: {
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.padding("12px"),
    ...shorthands.borderRadius("8px"),
    marginTop: "8px",
    "& h1": {
      fontSize: tokens.fontSizeBase600,
      fontWeight: tokens.fontWeightSemibold,
      marginTop: "16px",
      marginBottom: "8px",
      ":first-child": {
        marginTop: 0,
      },
    },
    "& h2": {
      fontSize: tokens.fontSizeBase500,
      fontWeight: tokens.fontWeightSemibold,
      marginTop: "12px",
      marginBottom: "6px",
    },
    "& h3": {
      fontSize: tokens.fontSizeBase400,
      fontWeight: tokens.fontWeightSemibold,
      marginTop: "8px",
      marginBottom: "4px",
    },
    "& p": {
      marginTop: "4px",
      marginBottom: "4px",
    },
    "& ul, & ol": {
      marginTop: "8px",
      marginBottom: "8px",
      paddingLeft: "20px",
    },
    "& li": {
      marginTop: "4px",
      marginBottom: "4px",
    },
    "& a": {
      color: tokens.colorBrandForeground1,
      textDecoration: "none",
      ":hover": {
        textDecoration: "underline",
      },
    },
    "& code": {
      backgroundColor: tokens.colorNeutralBackground3,
      padding: "2px 4px",
      borderRadius: "4px",
      fontFamily: tokens.fontFamilyMonospace,
      fontSize: tokens.fontSizeBase200,
    },
    "& pre": {
      backgroundColor: tokens.colorNeutralBackground3,
      padding: "12px",
      borderRadius: "8px",
      overflowX: "auto",
      marginTop: "8px",
      marginBottom: "8px",
    },
    "& pre code": {
      backgroundColor: "transparent",
      padding: 0,
    },
    "& blockquote": {
      borderLeft: `4px solid ${tokens.colorBrandBackground}`,
      paddingLeft: "12px",
      marginLeft: 0,
      marginTop: "8px",
      marginBottom: "8px",
      opacity: 0.8,
    },
  },
});

interface Question {
  index: number;
  question: string;
  context: string;
  answered: boolean;
}

interface RoutingDecision {
  workflow_type: string;
  confidence: number;
  reasoning: string;
  extracted_params?: any;
}

interface Message {
  id: string;
  type: "user" | "system" | "questions" | "result" | "routing";
  content: string;
  workflowType?: string;
  workflowId?: string;
  status?: string;
  timestamp: Date;
  questions?: Question[];
  routingDecision?: RoutingDecision;
}

const API_BASE_URL = "http://localhost:8005";

function App() {
  const styles = useStyles();

  // Load messages from localStorage on initial mount
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const saved = localStorage.getItem("chat-messages");
      if (saved) {
        const parsed = JSON.parse(saved);
        // Convert timestamp strings back to Date objects
        return parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
      }
    } catch (error) {
      console.error("Failed to load messages from localStorage:", error);
    }
    return [];
  });

  const [inputValue, setInputValue] = useState("");
  const [selectedWorkflow, setSelectedWorkflow] =
    useState<string>("orchestrator");
  const [isLoading, setIsLoading] = useState(false);
  const [activeWorkflows, setActiveWorkflows] = useState<Map<string, any>>(
    new Map()
  );
  const [questionAnswers, setQuestionAnswers] = useState<Map<string, string>>(
    new Map()
  );
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const prevMessageCountRef = useRef<number>(0);

  // Save messages to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem("chat-messages", JSON.stringify(messages));
    } catch (error) {
      console.error("Failed to save messages to localStorage:", error);
    }
  }, [messages]);

  // WebSocket connection
  useEffect(() => {
    const clientId = "ui-user";
    const ws = new WebSocket(`ws://localhost:8005/ws/${clientId}`);

    ws.onopen = () => {
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("WebSocket message:", data);

      if (data.type === "workflow_result") {
        // Format result based on workflow type
        let formattedContent = "";

        // Check if this is an orchestrator result
        if (data.result.selected_workflow) {
          const workflowType = data.result.selected_workflow;

          if (workflowType === "direct_llm") {
            // For direct LLM responses (jokes, simple questions)
            formattedContent = data.result.result.response;
          } else if (workflowType === "deep_research") {
            // For research results - format nicely
            const resResult = data.result.result;
            if (resResult.detailed_findings) {
              formattedContent = `## Summary\n\n${resResult.research_summary}\n\n---\n\n## Detailed Findings\n\n${resResult.detailed_findings}`;

              if (resResult.sources && resResult.sources.length > 0) {
                formattedContent += `\n\n---\n\n## Sources\n\n${resResult.sources.map((s: string, i: number) => `${i + 1}. ${s}`).join('\n')}`;
              }
            } else {
              formattedContent = resResult.research_summary || JSON.stringify(resResult, null, 2);
            }
          } else if (workflowType === "code_analysis") {
            // For code analysis results - format nicely
            const codeResult = data.result.result;
            formattedContent = `**Repository:** ${codeResult.repository}\n`;
            formattedContent += `**Analysis Type:** ${codeResult.analysis_type}\n`;
            formattedContent += `**Issues Found:** ${codeResult.issues_found}\n\n`;
            formattedContent += `---\n\n`;

            if (codeResult.critical_issues && codeResult.critical_issues.length > 0) {
              formattedContent += `## Critical Issues\n\n`;
              codeResult.critical_issues.forEach((issue: string, i: number) => {
                formattedContent += `${i + 1}. ${issue}\n`;
              });
              formattedContent += `\n`;
            }

            if (codeResult.recommendations && codeResult.recommendations.length > 0) {
              formattedContent += `## Recommendations\n\n`;
              codeResult.recommendations.forEach((rec: string, i: number) => {
                formattedContent += `${i + 1}. ${rec}\n`;
              });
              formattedContent += `\n`;
            }

            if (codeResult.refactoring_suggestions && codeResult.refactoring_suggestions.length > 0) {
              formattedContent += `## Refactoring Suggestions\n\n`;
              codeResult.refactoring_suggestions.forEach((sug: string, i: number) => {
                formattedContent += `${i + 1}. ${sug}\n`;
              });
            }
          } else if (workflowType === "content_generation") {
            // For content generation results - format nicely
            const contentResult = data.result.result;
            formattedContent = `**Topic:** ${contentResult.topic}\n`;
            formattedContent += `**Content Type:** ${contentResult.content_type}\n`;
            formattedContent += `**Word Count:** ${contentResult.word_count}\n`;
            formattedContent += `**Readability Score:** ${contentResult.readability_score}\n`;

            if (contentResult.seo_keywords && contentResult.seo_keywords.length > 0) {
              formattedContent += `**SEO Keywords:** ${contentResult.seo_keywords.join(', ')}\n`;
            }

            formattedContent += `\n---\n\n`;
            formattedContent += contentResult.generated_content;
          } else {
            formattedContent = JSON.stringify(data.result, null, 2);
          }
        } else {
          // Direct workflow results (not through orchestrator)
          formattedContent =
            data.result.detailed_findings ||
            data.result.research_summary ||
            data.result.response ||
            JSON.stringify(data.result, null, 2);
        }

        const resultMessage: Message = {
          id: `result-${Date.now()}`,
          type: "result",
          content: formattedContent,
          workflowId: data.workflow_id,
          status: "completed",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, resultMessage]);

        // Remove from active workflows
        setActiveWorkflows((prev) => {
          const updated = new Map(prev);
          updated.delete(data.workflow_id);
          return updated;
        });
      } else if (data.type === "workflow_error") {
        // Add error message
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          type: "system",
          content: `Error: ${data.error}`,
          workflowId: data.workflow_id,
          status: "failed",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, []);

  // Auto-scroll to bottom only when NEW messages are added (not on status updates)
  useEffect(() => {
    if (chatContainerRef.current) {
      const container = chatContainerRef.current;
      const currentMessageCount = messages.length;
      const messageCountChanged = currentMessageCount !== prevMessageCountRef.current;

      // Only auto-scroll if:
      // 1. A new message was added (not just a status update)
      // 2. User is already near the bottom (within 100px)
      if (messageCountChanged) {
        const isNearBottom =
          container.scrollHeight - container.scrollTop - container.clientHeight < 100;

        if (isNearBottom) {
          container.scrollTop = container.scrollHeight;
        }

        // Update the ref with current count
        prevMessageCountRef.current = currentMessageCount;
      }
    }
  }, [messages]);

  // Poll active workflows for status updates and questions
  useEffect(() => {
    const interval = setInterval(async () => {
      const workflowIds = Array.from(activeWorkflows.keys());

      for (const workflowId of workflowIds) {
        try {
          const statusResponse = await axios.get(
            `${API_BASE_URL}/workflow/${workflowId}/status`
          );
          const status = statusResponse.data;

          console.log(`Workflow ${workflowId.substring(0, 30)}... type: ${status.type}, status:`, status.status);

          setActiveWorkflows((prev) => {
            const updated = new Map(prev);
            updated.set(workflowId, status);
            return updated;
          });

          // Update message with a friendly status (not raw JSON)
          let friendlyStatus = "running";
          if (status.status?.current_status) {
            friendlyStatus = status.status.current_status.replace(/_/g, " ");
          }

          setMessages((prev) =>
            prev.map((msg) =>
              msg.workflowId === workflowId
                ? { ...msg, status: friendlyStatus }
                : msg
            )
          );

          // For orchestrator workflows, fetch routing decision and track sub-workflow
          if (status.type === "orchestrator") {
            const routingMessageExists = messages.some(
              (msg) => msg.workflowId === workflowId && msg.type === "routing"
            );

            if (!routingMessageExists && status.status?.routing_decision) {
              const routingMessage: Message = {
                id: `routing-${workflowId}`,
                type: "routing",
                content: `Routing Decision: ${status.status.routing_decision.workflow_type}`,
                workflowType: "orchestrator",
                workflowId: workflowId,
                routingDecision: status.status.routing_decision,
                timestamp: new Date(),
              };

              setMessages((prev) => [...prev, routingMessage]);
            }

            // Track sub-workflow if orchestrator is executing one
            if (status.status?.sub_workflow_id) {
              const subWorkflowId = status.status.sub_workflow_id;
              console.log(`Orchestrator has sub-workflow: ${subWorkflowId}`);

              // Add sub-workflow to active workflows if not already there
              if (!activeWorkflows.has(subWorkflowId)) {
                console.log(`Adding sub-workflow ${subWorkflowId} to tracking`);
                setActiveWorkflows((prev) => {
                  const updated = new Map(prev);
                  updated.set(subWorkflowId, { status: "running" });
                  return updated;
                });
              }
            }
          }

          // For deep_research workflows, fetch questions if waiting
          if (status.type === "deep_research") {
            console.log(`Deep research workflow ${workflowId}:`, status.status);

            if (status.status?.waiting_for_ui) {
              console.log(`Fetching questions for workflow ${workflowId}`);

              const questionsResponse = await axios.get(
                `${API_BASE_URL}/workflow/${workflowId}/questions`
              );
              const questions = questionsResponse.data.questions;

              console.log(`Received ${questions.length} questions:`, questions);

              // Check if we already have a questions message for this workflow
              const questionsMessageExists = messages.some(
                (msg) => msg.workflowId === workflowId && msg.type === "questions"
              );

              // Only add questions message once
              if (!questionsMessageExists && questions.length > 0) {
                console.log(`Adding questions message for workflow ${workflowId}`);

                const questionsMessage: Message = {
                  id: `questions-${workflowId}`,
                  type: "questions",
                  content: "Please answer the following clarifying questions:",
                  workflowType: "deep_research",
                  workflowId: workflowId,
                  questions: questions,
                  timestamp: new Date(),
                };

                setMessages((prev) => [...prev, questionsMessage]);
              } else {
                console.log(`Questions already exist or no questions for ${workflowId}`);
              }
            }
          }
        } catch (error) {
          console.error(`Failed to poll workflow ${workflowId}:`, error);
        }
      }
    }, 3000); // Poll every 3 seconds

    return () => clearInterval(interval);
  }, [activeWorkflows, messages]);

  const getWorkflowIcon = (type: string) => {
    switch (type) {
      case "orchestrator":
        return <BrainCircuit24Regular />;
      case "deep_research":
        return <BrainCircuit24Regular />;
      case "code_analysis":
        return <Code24Regular />;
      case "content_generation":
        return <Document24Regular />;
      case "direct_llm":
        return <BrainCircuit24Regular />;
      default:
        return null;
    }
  };

  const getWorkflowLabel = (type: string) => {
    switch (type) {
      case "orchestrator":
        return "Smart Routing";
      case "deep_research":
        return "Deep Research";
      case "code_analysis":
        return "Code Analysis";
      case "content_generation":
        return "Content Generation";
      case "direct_llm":
        return "Direct Chat";
      default:
        return type;
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      type: "user",
      content: inputValue,
      workflowType: selectedWorkflow,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      let response;
      let workflowId;

      // Start appropriate workflow based on selection
      switch (selectedWorkflow) {
        case "orchestrator":
          response = await axios.post(`${API_BASE_URL}/orchestrator/start`, {
            message: inputValue,
            user_id: "ui-user",
          });
          workflowId = response.data.workflow_id;
          break;

        case "deep_research":
          response = await axios.post(`${API_BASE_URL}/research/start`, {
            task: inputValue,
            user_id: "ui-user",
          });
          workflowId = response.data.workflow_id;
          break;

        case "code_analysis":
          response = await axios.post(`${API_BASE_URL}/code-analysis/start`, {
            repository_path: inputValue,
            analysis_type: "security",
            user_id: "ui-user",
          });
          workflowId = response.data.workflow_id;
          break;

        case "content_generation":
          response = await axios.post(`${API_BASE_URL}/content/start`, {
            topic: inputValue,
            content_type: "blog",
            target_audience: "developers",
            tone: "professional",
            length: "medium",
            user_id: "ui-user",
          });
          workflowId = response.data.workflow_id;
          break;

        default:
          throw new Error("Invalid workflow type");
      }

      // Add workflow to active tracking
      setActiveWorkflows((prev) =>
        new Map(prev).set(workflowId, { status: "started" })
      );

      const systemMessage: Message = {
        id: `system-${Date.now()}`,
        type: "system",
        content: response.data.message,
        workflowType: selectedWorkflow,
        workflowId: workflowId,
        status: "running",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, systemMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        type: "system",
        content: `Error: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const submitAllAnswers = async (
    workflowId: string,
    answers: Map<number, string>
  ) => {
    try {
      // Send all answers to the workflow
      for (const [questionIndex, answer] of answers.entries()) {
        if (answer.trim()) {
          await axios.post(`${API_BASE_URL}/workflow/${workflowId}/answer`, {
            answer: answer,
            question_index: questionIndex,
          });
        }
      }

      // Remove questions message and add answers as user message
      setMessages((prev) =>
        prev.filter(
          (msg) => !(msg.workflowId === workflowId && msg.type === "questions")
        )
      );

      // Add user's answers as a message with markdown formatting
      const answersText = Array.from(answers.entries())
        .map(([idx, ans]) => `**Question ${idx + 1}:** ${ans}`)
        .join("\n\n");

      const answerMessage: Message = {
        id: `answers-${Date.now()}`,
        type: "user",
        content: `### My Answers\n\n${answersText}`,
        workflowId: workflowId,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, answerMessage]);
    } catch (error: any) {
      console.error("Failed to answer questions:", error);
    }
  };

  const clearChat = () => {
    if (window.confirm("Are you sure you want to clear all messages?")) {
      setMessages([]);
      localStorage.removeItem("chat-messages");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerTitle}>
          <Text size={600} weight="semibold">
            Complex AI Workflows
          </Text>
          <Text size={300}>Powered by Temporal and OpenAI Agents</Text>
        </div>
        {messages.length > 0 && (
          <Button
            appearance="subtle"
            icon={<Delete24Regular />}
            onClick={clearChat}
            style={{ color: tokens.colorNeutralForegroundOnBrand }}
          >
            Clear Chat
          </Button>
        )}
      </div>

      <div className={styles.main}>
        <div className={styles.chatContainer} ref={chatContainerRef}>
          {messages.length === 0 && (
            <Card className={styles.systemMessage}>
              <CardHeader
                header={<Text weight="semibold">Welcome!</Text>}
                description={
                  <Text>
                    Select a workflow and send a message to get started. Your
                    workflows will interact with AI agents and Slack for human
                    approval.
                  </Text>
                }
              />
            </Card>
          )}

          {messages.map((msg) => (
            <Card
              key={msg.id}
              className={
                msg.type === "user" ? styles.userMessage : styles.systemMessage
              }
            >
              <CardHeader
                image={
                  msg.workflowType
                    ? getWorkflowIcon(msg.workflowType)
                    : undefined
                }
                header={
                  <Text weight="semibold">
                    {msg.type === "user"
                      ? "You"
                      : msg.workflowType
                      ? getWorkflowLabel(msg.workflowType)
                      : "System"}
                  </Text>
                }
                description={
                  <Text size={200}>{msg.timestamp.toLocaleTimeString()}</Text>
                }
              />
              <div className={styles.markdownContent}>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: ({ node, ...props }) => (
                      <a {...props} target="_blank" rel="noopener noreferrer" />
                    ),
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              </div>

              {/* Routing Decision Display */}
              {msg.type === "routing" && msg.routingDecision && (
                <div
                  style={{
                    marginTop: "16px",
                    padding: "12px",
                    backgroundColor: tokens.colorNeutralBackground3,
                    borderRadius: "8px",
                  }}
                >
                  <Text weight="semibold" block style={{ marginBottom: "8px" }}>
                    🎯 Selected Workflow: {getWorkflowLabel(msg.routingDecision.workflow_type)}
                  </Text>
                  <Text size={200} block style={{ marginBottom: "4px" }}>
                    Confidence: {(msg.routingDecision.confidence * 100).toFixed(1)}%
                  </Text>
                  <Text size={200} block style={{ opacity: 0.8 }}>
                    Reasoning: {msg.routingDecision.reasoning}
                  </Text>
                  {msg.routingDecision.extracted_params &&
                    Object.keys(msg.routingDecision.extracted_params).length > 0 && (
                      <Text size={200} block style={{ marginTop: "8px", opacity: 0.7 }}>
                        Parameters: {JSON.stringify(msg.routingDecision.extracted_params, null, 2)}
                      </Text>
                    )}
                  <Badge
                    appearance="outline"
                    color="success"
                    style={{ marginTop: "8px" }}
                  >
                    {getWorkflowIcon(msg.routingDecision.workflow_type)} Processing with {getWorkflowLabel(msg.routingDecision.workflow_type)}
                  </Badge>
                </div>
              )}

              {/* Questions with multiple inputs */}
              {msg.type === "questions" && msg.questions && msg.workflowId && (
                <div style={{ marginTop: "16px" }}>
                  {msg.questions.map((q) => (
                    <div
                      key={q.index}
                      style={{
                        marginBottom: "16px",
                        padding: "12px",
                        backgroundColor: tokens.colorNeutralBackground3,
                        borderRadius: "8px",
                      }}
                    >
                      <Text weight="semibold" block style={{ marginBottom: "8px" }}>
                        Question {q.index + 1}: {q.question}
                      </Text>
                      {q.context && (
                        <Text size={200} block style={{ marginBottom: "8px", opacity: 0.8 }}>
                          Context: {q.context}
                        </Text>
                      )}
                      <Textarea
                        placeholder="Type your answer..."
                        resize="vertical"
                        rows={5}
                        style={{ width: "100%" }}
                        value={
                          questionAnswers.get(
                            `${msg.workflowId}-${q.index}`
                          ) || ""
                        }
                        onChange={(e) => {
                          const key = `${msg.workflowId}-${q.index}`;
                          setQuestionAnswers((prev) => {
                            const updated = new Map(prev);
                            updated.set(key, e.target.value);
                            return updated;
                          });
                        }}
                      />
                    </div>
                  ))}
                  <Button
                    appearance="primary"
                    onClick={() => {
                      if (msg.workflowId && msg.questions) {
                        const answers = new Map<number, string>();
                        msg.questions.forEach((q) => {
                          const key = `${msg.workflowId}-${q.index}`;
                          const answer = questionAnswers.get(key) || "";
                          answers.set(q.index, answer);
                        });
                        submitAllAnswers(msg.workflowId, answers);
                        // Clear question answers
                        setQuestionAnswers(new Map());
                      }
                    }}
                  >
                    Submit All Answers
                  </Button>
                </div>
              )}

              {msg.workflowId && msg.type !== "questions" && (
                <div className={styles.activityBadge}>
                  <Badge
                    appearance="outline"
                    color={
                      msg.status === "completed" ? "success" : "informative"
                    }
                    icon={
                      msg.status === "completed" ? (
                        <CheckmarkCircle24Regular />
                      ) : (
                        <Clock24Regular />
                      )
                    }
                  >
                    Workflow ID: {msg.workflowId.slice(0, 20)}...
                  </Badge>
                  {msg.status && (
                    <Text size={200} block style={{ marginTop: "4px" }}>
                      Status: {msg.status}
                    </Text>
                  )}
                </div>
              )}
            </Card>
          ))}

          {isLoading && (
            <Card className={styles.systemMessage}>
              <Spinner size="small" label="Processing..." />
            </Card>
          )}
        </div>

        <div className={styles.inputContainer}>
          <Dropdown
            className={styles.workflowSelector}
            placeholder="Select workflow"
            value={getWorkflowLabel(selectedWorkflow)}
            selectedOptions={[selectedWorkflow]}
            onOptionSelect={(_, data) =>
              setSelectedWorkflow(data.optionValue as string)
            }
          >
            <Option value="orchestrator" text="Smart Routing">
              <BrainCircuit24Regular /> Smart Routing (Recommended)
            </Option>
            <Option value="deep_research" text="Deep Research">
              <BrainCircuit24Regular /> Deep Research
            </Option>
            <Option value="code_analysis" text="Code Analysis">
              <Code24Regular /> Code Analysis
            </Option>
            <Option value="content_generation" text="Content Generation">
              <Document24Regular /> Content Generation
            </Option>
          </Dropdown>

          <Input
            className={styles.messageInput}
            placeholder="Type your message..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
          />

          <Button
            appearance="primary"
            icon={<Send24Regular />}
            onClick={sendMessage}
            disabled={isLoading || !inputValue.trim()}
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}

export default App;
