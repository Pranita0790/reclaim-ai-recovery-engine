import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { checkApiHealth } from "../../services/api";
import { Sidebar } from "./Sidebar";

export function AppLayout() {
  const [apiOnline, setApiOnline] = useState(false);
  useEffect(() => { const refresh = () => checkApiHealth().then(setApiOnline); refresh(); const interval = window.setInterval(refresh, 5000); return () => window.clearInterval(interval); }, []);
  return <div className="app-shell"><Sidebar apiOnline={apiOnline} /><main className="main-content"><div className="topbar"><span className="topbar-context">Recovery operations <span>/</span> Decision intelligence</span><div className="topbar-right"><span className="api-status"><span className={`status-dot ${apiOnline ? "online" : "offline"}`} />API {apiOnline ? "connected" : "offline"}</span><div className="avatar">OP</div></div></div><div className="page-content"><Outlet /></div></main></div>;
}
