import { useEffect, useState } from "react";

/*
  IMPORTANT:
  This uses the Vite proxy configured in vite.config.ts.

  Browser:
  localhost:5173/api/v1/recovery/process

  Vite forwards internally to:
  127.0.0.1:8000/api/v1/recovery/process
*/
const API_BASE_URL = "/api/v1";

type RecoveryResult = {
  case_id: string;
  recommended_action: string;
  decision_status: string;
  confidence: number;
  expected_recovery: number;
  expected_value: number;
  explanation: string;
  execution_status: string;
  execution_message: string;
  external_reference: string | null;
  final_state: string;
};

function App() {
  // --------------------------------------------------
  // FORM STATE
  // --------------------------------------------------

  const [caseId, setCaseId] = useState("MANUAL-TEST-001");
  const [customerId, setCustomerId] = useState("CUSTOMER-001");

  const [amount, setAmount] = useState("5000");
  const [currency, setCurrency] = useState("INR");

  const [paymentStatus, setPaymentStatus] = useState("FAILED");

  const [failureReason, setFailureReason] =
    useState("INSUFFICIENT_FUNDS");

  const [failureCount, setFailureCount] = useState("1");

  const [customerAttempts, setCustomerAttempts] = useState("0");

  const [daysSinceFailure, setDaysSinceFailure] = useState("1");

  const [isCustomerActive, setIsCustomerActive] =
    useState(true);

  const [
    hasValidPaymentMethod,
    setHasValidPaymentMethod,
  ] = useState(true);

  // --------------------------------------------------
  // APPLICATION STATE
  // --------------------------------------------------

  const [apiOnline, setApiOnline] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const [result, setResult] =
    useState<RecoveryResult | null>(null);

  const [pipelineStep, setPipelineStep] =
    useState(0);

  // --------------------------------------------------
  // API HEALTH CHECK
  // --------------------------------------------------

  const checkApiHealth = async () => {
    try {
      const response = await fetch("/health");

      setApiOnline(response.ok);
    } catch {
      setApiOnline(false);
    }
  };

  useEffect(() => {
    checkApiHealth();

    const interval = setInterval(
      checkApiHealth,
      5000
    );

    return () => clearInterval(interval);
  }, []);

  // --------------------------------------------------
  // RUN RECOVERY ANALYSIS
  // --------------------------------------------------

  const handleRunAnalysis = async () => {
    setError("");
    setResult(null);
    setIsLoading(true);
    setPipelineStep(1);

    try {
      const payload = {
        case_id: caseId,
        customer_id: customerId,
        amount: Number(amount),
        currency,
        payment_status: paymentStatus,
        failure_reason: failureReason,
        failure_count: Number(failureCount),
        customer_attempt_count: Number(customerAttempts),
        days_since_failure: Number(daysSinceFailure),
        is_customer_active: isCustomerActive,
        has_valid_payment_method:
          hasValidPaymentMethod,
      };

      // --------------------------------------------------
      // PIPELINE ANIMATION
      // --------------------------------------------------

      setPipelineStep(2);

      await new Promise((resolve) =>
        setTimeout(resolve, 250)
      );

      setPipelineStep(3);

      await new Promise((resolve) =>
        setTimeout(resolve, 250)
      );

      setPipelineStep(4);

      await new Promise((resolve) =>
        setTimeout(resolve, 250)
      );

      // --------------------------------------------------
      // API REQUEST
      // --------------------------------------------------

      const response = await fetch(
        `${API_BASE_URL}/recovery/process`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify(payload),
        }
      );

      // --------------------------------------------------
      // HANDLE API ERROR
      // --------------------------------------------------

      if (!response.ok) {
        let message =
          "Unable to process recovery case.";

        try {
          const errorData =
            await response.json();

          message =
            errorData.message ||
            errorData.detail ||
            message;
        } catch {
          // Keep default message.
        }

        throw new Error(message);
      }

      // --------------------------------------------------
      // SUCCESS RESPONSE
      // --------------------------------------------------

      const data: RecoveryResult =
        await response.json();

      setPipelineStep(5);

      await new Promise((resolve) =>
        setTimeout(resolve, 250)
      );

      setPipelineStep(6);

      await new Promise((resolve) =>
        setTimeout(resolve, 250)
      );

      setPipelineStep(7);

      await new Promise((resolve) =>
        setTimeout(resolve, 250)
      );

      setPipelineStep(8);

      setResult(data);

      // Refresh backend status
      checkApiHealth();
    } catch (err) {
      console.error(
        "Recovery API request failed:",
        err
      );

      setPipelineStep(0);

      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(
          "Something went wrong while processing the recovery case."
        );
      }
    } finally {
      setIsLoading(false);
    }
  };

  // --------------------------------------------------
  // RESET FORM
  // --------------------------------------------------

  const handleReset = () => {
    setCaseId("MANUAL-TEST-001");
    setCustomerId("CUSTOMER-001");
    setAmount("5000");
    setCurrency("INR");
    setPaymentStatus("FAILED");
    setFailureReason("INSUFFICIENT_FUNDS");
    setFailureCount("1");
    setCustomerAttempts("0");
    setDaysSinceFailure("1");
    setIsCustomerActive(true);
    setHasValidPaymentMethod(true);

    setError("");
    setResult(null);
    setPipelineStep(0);
  };

  // --------------------------------------------------
  // PIPELINE DATA
  // --------------------------------------------------

  const pipelineSteps = [
    {
      number: 1,
      label: "RECEIVE",
      description: "Case received",
    },
    {
      number: 2,
      label: "POLICY",
      description: "Policy evaluated",
    },
    {
      number: 3,
      label: "BASELINE",
      description: "Baseline estimated",
    },
    {
      number: 4,
      label: "ML",
      description: "ML model consulted",
    },
    {
      number: 5,
      label: "ACTIONS",
      description: "Actions evaluated",
    },
    {
      number: 6,
      label: "DECIDE",
      description: "Best action selected",
    },
    {
      number: 7,
      label: "EXECUTE",
      description: "Execution",
    },
    {
      number: 8,
      label: "RESULT",
      description: "Final result",
    },
  ];

  // --------------------------------------------------
  // HELPERS
  // --------------------------------------------------

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat(
      "en-IN",
      {
        style: "currency",
        currency,
        maximumFractionDigits: 2,
      }
    ).format(value);
  };

  // --------------------------------------------------
  // UI
  // --------------------------------------------------

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#090a0f",
        color: "#e7e7eb",
        fontFamily:
          "Inter, system-ui, sans-serif",
        display: "flex",
      }}
    >
      {/* SIDEBAR */}

      <aside
        style={{
          width: "310px",
          borderRight:
            "1px solid #242632",
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          background: "#0b0c12",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            padding: "28px 26px",
            borderBottom:
              "1px solid #242632",
          }}
        >
          <div
            style={{
              display: "flex",
              gap: "12px",
              alignItems: "center",
            }}
          >
            <div
              style={{
                width: "34px",
                height: "34px",
                borderRadius: "10px",
                border:
                  "1px solid #4c55a8",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#9da8ff",
                fontWeight: 700,
              }}
            >
              R
            </div>

            <div>
              <div
                style={{
                  fontWeight: 700,
                  letterSpacing: "1px",
                }}
              >
                RECLAIM
              </div>

              <div
                style={{
                  color: "#7d8190",
                  fontSize: "12px",
                  marginTop: "3px",
                }}
              >
                AI Recovery Engine
              </div>
            </div>
          </div>
        </div>

        <div
          style={{
            padding: "26px 18px",
          }}
        >
          <div
            style={{
              fontSize: "11px",
              letterSpacing: "2px",
              color: "#777b89",
              marginBottom: "14px",
              paddingLeft: "10px",
            }}
          >
            WORKSPACE
          </div>

          <div
            style={{
              padding: "14px",
              borderRadius: "8px",
              background: "#171727",
              border:
                "1px solid #34366d",
              marginBottom: "6px",
            }}
          >
            ◇ &nbsp; Overview
          </div>

          <div
            style={{
              padding: "14px",
              color: "#a4a6b0",
            }}
          >
            ⌁ &nbsp; Analyze Recovery
          </div>

          <div
            style={{
              padding: "14px",
              color: "#a4a6b0",
            }}
          >
            ▫ &nbsp; Recovery Cases
          </div>

          <div
            style={{
              fontSize: "11px",
              letterSpacing: "2px",
              color: "#777b89",
              margin:
                "32px 0 14px 10px",
            }}
          >
            GOVERNANCE
          </div>

          <div
            style={{
              padding: "14px",
              color: "#a4a6b0",
            }}
          >
            ◦ &nbsp; Activity & Audit
          </div>
        </div>

        <div
          style={{
            marginTop: "auto",
            borderTop:
              "1px solid #242632",
            padding: "22px",
            display: "flex",
            justifyContent:
              "space-between",
            color: "#8e919c",
            fontSize: "12px",
          }}
        >
          <span>
            <span
              style={{
                color: apiOnline
                  ? "#42d392"
                  : "#f26d6d",
              }}
            >
              ●
            </span>{" "}
            Engine{" "}
            {apiOnline
              ? "operational"
              : "offline"}
          </span>

          <span>v0.1.0</span>
        </div>
      </aside>

      {/* MAIN */}

      <main
        style={{
          flex: 1,
          minWidth: 0,
        }}
      >
        <div
          style={{
            padding: "24px 38px",
          }}
        >
          {/* CONTENT GRID */}

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "minmax(500px, 1.1fr) minmax(500px, 1fr)",
              gap: "18px",
            }}
          >
            {/* FORM */}

            <section
              style={{
                background: "#111218",
                border:
                  "1px solid #292b35",
                borderRadius: "12px",
                padding: "26px",
              }}
            >
              <div
                style={{
                  color: "#858999",
                  fontSize: "10px",
                  letterSpacing: "2px",
                }}
              >
                RECOVERY CASE
              </div>

              <h2
                style={{
                  margin:
                    "8px 0 28px 0",
                  fontSize: "18px",
                }}
              >
                Case context
              </h2>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "1fr 1fr",
                  gap: "18px",
                }}
              >
                <Field
                  label="CASE ID"
                  value={caseId}
                  onChange={setCaseId}
                />

                <Field
                  label="CUSTOMER ID"
                  value={customerId}
                  onChange={setCustomerId}
                />

                <Field
                  label="AMOUNT"
                  type="number"
                  value={amount}
                  onChange={setAmount}
                />

                <Field
                  label="CURRENCY"
                  value={currency}
                  onChange={setCurrency}
                />

                <SelectField
                  label="PAYMENT STATUS"
                  value={paymentStatus}
                  onChange={
                    setPaymentStatus
                  }
                  options={[
                    "FAILED",
                    "PENDING",
                    "SUCCESS",
                  ]}
                />

                <SelectField
                  label="FAILURE REASON"
                  value={failureReason}
                  onChange={
                    setFailureReason
                  }
                  options={[
                    "INSUFFICIENT_FUNDS",
                    "CARD_DECLINED",
                    "NETWORK_ERROR",
                    "EXPIRED_CARD",
                    "UNKNOWN",
                  ]}
                />

                <Field
                  label="FAILURE COUNT"
                  type="number"
                  value={failureCount}
                  onChange={setFailureCount}
                />

                <Field
                  label="CUSTOMER ATTEMPTS"
                  type="number"
                  value={
                    customerAttempts
                  }
                  onChange={
                    setCustomerAttempts
                  }
                />

                <Field
                  label="DAYS SINCE FAILURE"
                  type="number"
                  value={
                    daysSinceFailure
                  }
                  onChange={
                    setDaysSinceFailure
                  }
                />
              </div>

              <div
                style={{
                  display: "flex",
                  gap: "12px",
                  marginTop: "22px",
                }}
              >
                <Toggle
                  label="Customer active"
                  active={
                    isCustomerActive
                  }
                  onClick={() =>
                    setIsCustomerActive(
                      !isCustomerActive
                    )
                  }
                />

                <Toggle
                  label="Valid payment method"
                  active={
                    hasValidPaymentMethod
                  }
                  onClick={() =>
                    setHasValidPaymentMethod(
                      !hasValidPaymentMethod
                    )
                  }
                />
              </div>

              {error && (
                <div
                  style={{
                    color: "#ef8d83",
                    marginTop: "20px",
                    padding: "14px",
                    border:
                      "1px solid #663a38",
                    background:
                      "#24191a",
                    borderRadius: "8px",
                    fontSize: "14px",
                  }}
                >
                  {error}
                </div>
              )}

              <div
                style={{
                  borderTop:
                    "1px solid #292b35",
                  marginTop: "26px",
                  paddingTop: "22px",
                  display: "flex",
                  gap: "12px",
                }}
              >
                <button
                  onClick={
                    handleRunAnalysis
                  }
                  disabled={isLoading}
                  style={{
                    border: "none",
                    borderRadius: "7px",
                    padding:
                      "14px 20px",
                    fontWeight: 600,
                    cursor: isLoading
                      ? "not-allowed"
                      : "pointer",
                    background: "#5c5dd6",
                    color: "#ffffff",
                    opacity: isLoading
                      ? 0.7
                      : 1,
                  }}
                >
                  {isLoading
                    ? "Running analysis..."
                    : "Run recovery analysis →"}
                </button>

                <button
                  onClick={handleReset}
                  disabled={isLoading}
                  style={{
                    background:
                      "transparent",
                    color: "#c2c4ce",
                    border:
                      "1px solid #3a3c47",
                    borderRadius: "7px",
                    padding:
                      "14px 20px",
                    cursor: "pointer",
                  }}
                >
                  Reset
                </button>
              </div>
            </section>

            {/* PIPELINE */}

            <section
              style={{
                background: "#111218",
                border:
                  "1px solid #292b35",
                borderRadius: "12px",
                padding: "26px",
                minHeight: "500px",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent:
                    "space-between",
                }}
              >
                <div>
                  <div
                    style={{
                      color: "#858999",
                      fontSize: "10px",
                      letterSpacing: "2px",
                    }}
                  >
                    ENGINE
                  </div>

                  <h2
                    style={{
                      margin:
                        "8px 0 0 0",
                      fontSize: "18px",
                    }}
                  >
                    Recovery pipeline
                  </h2>
                </div>

                <div
                  style={{
                    border:
                      "1px solid #30323d",
                    borderRadius: "20px",
                    padding:
                      "7px 12px",
                    fontSize: "10px",
                    color: "#a5a8b5",
                    height: "fit-content",
                  }}
                >
                  {isLoading
                    ? "PROCESSING"
                    : result
                      ? "COMPLETE"
                      : "READY"}
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems:
                    "flex-start",
                  justifyContent:
                    "space-between",
                  marginTop: "40px",
                }}
              >
                {pipelineSteps.map(
                  (step) => {
                    const completed =
                      pipelineStep >
                      step.number;

                    const active =
                      pipelineStep ===
                      step.number;

                    return (
                      <div
                        key={step.number}
                        style={{
                          flex: 1,
                          textAlign:
                            "center",
                          position:
                            "relative",
                        }}
                      >
                        <div
                          style={{
                            width:
                              "38px",
                            height:
                              "38px",
                            margin:
                              "0 auto 12px",
                            borderRadius:
                              "50%",
                            border: active
                              ? "2px solid #6a6fe5"
                              : completed
                                ? "1px solid #555bc7"
                                : "1px solid #353743",
                            display:
                              "flex",
                            alignItems:
                              "center",
                            justifyContent:
                              "center",
                            color:
                              completed
                                ? "#9ca6ff"
                                : active
                                  ? "#ffffff"
                                  : "#8a8d98",
                            background:
                              active
                                ? "#1d1f38"
                                : "#15161c",
                          }}
                        >
                          {completed
                            ? "✓"
                            : step.number}
                        </div>

                        <div
                          style={{
                            fontSize:
                              "9px",
                            fontWeight: 700,
                            letterSpacing:
                              "1px",
                          }}
                        >
                          {step.label}
                        </div>

                        <div
                          style={{
                            fontSize:
                              "8px",
                            color:
                              "#7e818d",
                            marginTop:
                              "7px",
                            lineHeight: 1.4,
                          }}
                        >
                          {
                            step.description
                          }
                        </div>
                      </div>
                    );
                  }
                )}
              </div>

              <div
                style={{
                  marginTop: "auto",
                  background:
                    "#17181e",
                  border:
                    "1px solid #292b35",
                  borderRadius:
                    "10px",
                  padding: "20px",
                }}
              >
                <div
                  style={{
                    fontSize: "10px",
                    letterSpacing:
                      "2px",
                    color: "#8995d6",
                    marginBottom:
                      "12px",
                  }}
                >
                  {result
                    ? "RECOVERY COMPLETE"
                    : "ACTION EVALUATION"}
                </div>

                <div
                  style={{
                    color: "#aeb0ba",
                    lineHeight: 1.6,
                    fontSize: "14px",
                  }}
                >
                  {result
                    ? result.explanation
                    : "Comparing available recovery actions against expected business value."}
                </div>
              </div>
            </section>
          </div>

          {/* RESULT */}

          {result && (
            <section
              style={{
                marginTop: "18px",
                background:
                  "#151622",
                border:
                  "1px solid #373b68",
                borderRadius: "12px",
                padding: "26px",
              }}
            >
              <div
                style={{
                  fontSize: "10px",
                  letterSpacing: "2px",
                  color: "#858999",
                  marginBottom: "15px",
                }}
              >
                DECISION RESULT
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "2fr 1fr 1fr 1fr",
                  gap: "25px",
                  alignItems:
                    "center",
                }}
              >
                <div>
                  <h2
                    style={{
                      margin: 0,
                      fontSize: "24px",
                    }}
                  >
                    {result.recommended_action.replace(
                      /_/g,
                      " "
                    )}
                  </h2>

                  <p
                    style={{
                      color: "#979aa6",
                      lineHeight: 1.5,
                      marginBottom: 0,
                    }}
                  >
                    {result.explanation}
                  </p>
                </div>

                <Metric
                  label="ENGINE CONFIDENCE"
                  value={formatPercent(
                    result.confidence
                  )}
                />

           <Metric
  label="EXPECTED RECOVERY"
  value={formatCurrency(result.expected_recovery)}
/>

                <Metric
                  label="EXPECTED VALUE"
                  value={formatCurrency(
                    result.expected_value
                  )}
                />
              </div>

              <div
                style={{
                  marginTop: "22px",
                  paddingTop: "18px",
                  borderTop:
                    "1px solid #292b35",
                  display: "flex",
                  gap: "35px",
                  color: "#a5a8b4",
                  fontSize: "13px",
                }}
              >
                <div>
                  Decision:{" "}
                  <strong>
                    {result.decision_status}
                  </strong>
                </div>

                <div>
                  Execution:{" "}
                  <strong>
                    {result.execution_status}
                  </strong>
                </div>

                <div>
                  {result.execution_message}
                </div>
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}


// --------------------------------------------------
// REUSABLE FIELD
// --------------------------------------------------

type FieldProps = {
  label: string;
  value: string;
  type?: string;
  onChange: (value: string) => void;
};

function Field({
  label,
  value,
  type = "text",
  onChange,
}: FieldProps) {
  return (
    <div>
      <label
        style={{
          display: "block",
          fontSize: "10px",
          letterSpacing: "2px",
          color: "#858999",
          marginBottom: "9px",
        }}
      >
        {label}
      </label>

      <input
        type={type}
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        style={{
          width: "100%",
          boxSizing: "border-box",
          background: "#15161c",
          border:
            "1px solid #363844",
          color: "#e6e7eb",
          borderRadius: "7px",
          padding: "13px",
          outline: "none",
        }}
      />
    </div>
  );
}


// --------------------------------------------------
// REUSABLE SELECT
// --------------------------------------------------

type SelectFieldProps = {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
};

function SelectField({
  label,
  value,
  options,
  onChange,
}: SelectFieldProps) {
  return (
    <div>
      <label
        style={{
          display: "block",
          fontSize: "10px",
          letterSpacing: "2px",
          color: "#858999",
          marginBottom: "9px",
        }}
      >
        {label}
      </label>

      <select
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        style={{
          width: "100%",
          background: "#15161c",
          border:
            "1px solid #363844",
          color: "#e6e7eb",
          borderRadius: "7px",
          padding: "13px",
          outline: "none",
        }}
      >
        {options.map(
          (option) => (
            <option
              key={option}
              value={option}
            >
              {option}
            </option>
          )
        )}
      </select>
    </div>
  );
}


// --------------------------------------------------
// TOGGLE
// --------------------------------------------------

type ToggleProps = {
  label: string;
  active: boolean;
  onClick: () => void;
};

function Toggle({
  label,
  active,
  onClick,
}: ToggleProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        background: active
          ? "#1a1b2d"
          : "#15161c",
        border: active
          ? "1px solid #454b91"
          : "1px solid #363844",
        color: "#d7d8df",
        borderRadius: "7px",
        padding: "10px 14px",
        cursor: "pointer",
        fontSize: "12px",
      }}
    >
      <span
        style={{
          color: active
            ? "#8894ff"
            : "#676a75",
        }}
      >
        ●
      </span>{" "}
      {label}
    </button>
  );
}


// --------------------------------------------------
// METRIC
// --------------------------------------------------

type MetricProps = {
  label: string;
  value: string;
};

function Metric({
  label,
  value,
}: MetricProps) {
  return (
    <div>
      <div
        style={{
          fontSize: "9px",
          letterSpacing: "2px",
          color: "#858999",
          marginBottom: "9px",
        }}
      >
        {label}
      </div>

      <div
        style={{
          fontSize: "17px",
          fontWeight: 600,
        }}
      >
        {value}
      </div>
    </div>
  );
}

export default App;