import { useState } from "react";
import { RouterProvider } from "react-router-dom";
import { router } from "./routes";
import { Login } from "./pages/Login";
import { isAuthenticated } from "./services/api";

export default function App() {
  const [authed, setAuthed] = useState(isAuthenticated());

  if (!authed) {
    return <Login onLogin={() => setAuthed(true)} />;
  }

  return <RouterProvider router={router} />;
}
