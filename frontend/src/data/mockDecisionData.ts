export const recoveryCases = [
  { id: "CASE-10482", customer: "CUSTOMER-001", amount: "₹5,000", action: "SMART_RETRY", quality: 92, status: "Executing", outcome: "₹2,940" },
  { id: "CASE-10479", customer: "CUSTOMER-044", amount: "₹1,800", action: "SEND_REMINDER", quality: 88, status: "Recovered", outcome: "₹1,280" },
  { id: "CASE-10471", customer: "CUSTOMER-117", amount: "₹12,400", action: "DO_NOTHING", quality: 76, status: "Policy blocked", outcome: "₹0" },
  { id: "CASE-10463", customer: "CUSTOMER-082", amount: "₹9,600", action: "ESCALATE", quality: 95, status: "Recovered", outcome: "₹8,500" },
];

export const auditEvents = [
  { time: "09:42:18.320", id: "DEC-10482", event: "Action selected", policy: "Passed", action: "SMART_RETRY", outcome: "Pending" },
  { time: "09:41:53.106", id: "DEC-10479", event: "Outcome verified", policy: "Passed", action: "SEND_REMINDER", outcome: "Recovered" },
  { time: "09:38:11.844", id: "DEC-10471", event: "Action blocked", policy: "Blocked", action: "DO_NOTHING", outcome: "No execution" },
  { time: "09:31:44.509", id: "DEC-10463", event: "Execution bounded", policy: "Passed", action: "ESCALATE", outcome: "Recovered" },
];

export const evaluationBenchmarks = [
  { label: "Economically optimal", value: "94.2%", width: 94 },
  { label: "Policy compliant", value: "98.7%", width: 99 },
  { label: "Better than baseline", value: "91.4%", width: 91 },
  { label: "Zero-regret decisions", value: "89.6%", width: 90 },
];
