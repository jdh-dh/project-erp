import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABELS } from "../utils/labels";

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="layout">
      <nav className="sidebar">
        <h1>개발 프로젝트 ERP</h1>
        <NavLink to="/projects">프로젝트</NavLink>
        <NavLink to="/customers">고객사</NavLink>
        {(user?.role === "admin" || user?.role === "manager") && (
          <NavLink to="/users">사용자</NavLink>
        )}
        <div className="spacer" />
        {user && (
          <div className="user">
            {user.name} ({ROLE_LABELS[user.role]})
          </div>
        )}
        <button className="secondary" onClick={logout}>
          로그아웃
        </button>
      </nav>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
