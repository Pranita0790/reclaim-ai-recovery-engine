import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { AuditTrail } from "./pages/AuditTrail";
import { DecisionReplay } from "./pages/DecisionReplay";
import { DecisionStudio } from "./pages/DecisionStudio";
import { EvaluationLab } from "./pages/EvaluationLab";
import { Overview } from "./pages/Overview";
import { RecoveryCases } from "./pages/RecoveryCases";

function App() {
  return <BrowserRouter><Routes><Route element={<AppLayout />}><Route index element={<Overview />} /><Route path="decision-studio" element={<DecisionStudio />} /><Route path="cases" element={<RecoveryCases />} /><Route path="replay" element={<DecisionReplay />} /><Route path="evaluation" element={<EvaluationLab />} /><Route path="audit" element={<AuditTrail />} /><Route path="*" element={<Navigate to="/" replace />} /></Route></Routes></BrowserRouter>;
}

export default App;
