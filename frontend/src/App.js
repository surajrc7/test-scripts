import React from "react";
import ReactDOM from "react-dom";
import CssBaseline from "@mui/material/CssBaseline";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { Box } from "@mui/material";
import { SnackbarProvider } from "notistack";

import SignUp from "./pages/Auth/SignUp";
import SignIn from "./pages/Auth/SignIn";
import Dashboard from "./pages/Home/Dashboard";
import AuthContextProvider from "./contexts/AuthContextProvider";
import RequireAuth from "./components/RequireAuth";
import RequireNotAuth from "./components/RequireNotAuth";
import BaseLayout from "./components/BaseLayout";
import RequestResetPassword from "./pages/Auth/RequestResetPassword";
import ResetPasswordConfirm from "./pages/Auth/ResetPasswordConfirm";
//import Tasks from "./pages/Tasks";
//import TaskDetails from "./pages/Tasks/TaskDetails";
//import Dashboard from "./pages/Dashboard";
import ThemeModeProvider from "./contexts/ThemeModeProvider";
import SwaggerApi from "./pages/SwaggerAPI";


export default function App() {
  return (
    <ThemeModeProvider>
      <CssBaseline />
      <AuthContextProvider>
        <SnackbarProvider>
          <Router>
            <Box
              sx={{
                bgcolor: (theme) => theme.palette.background.default,
                minHeight: "100vh",
                width: "100%",
              }}
            >
              <Routes>
                {/* <Route path="/admin" element={<Admin />} />*/}
                <Route path="/doc" element={<SwaggerApi />} />
   		 <Route element={<BaseLayout />}>
                   <Route path="/" element={<Dashboard />} />
                  </Route>
                <Route element={<RequireAuth />}>
   
                </Route>

                <Route element={<RequireNotAuth />}>
                  <Route path="/auth/signup" element={<SignUp />} />
                  <Route path="/auth/signin" element={<SignIn />} />
                  <Route
                    path="/auth/password-reset"
                    element={<RequestResetPassword />}
                  />
                  <Route
                    path="/auth/password-reset/confirm/:uid/:token"
                    element={<ResetPasswordConfirm />}
                  />
                </Route>
              </Routes>
            </Box>
          </Router>
        </SnackbarProvider>
      </AuthContextProvider>
    </ThemeModeProvider>
  );
}

ReactDOM.render(<App />, document.getElementById("root"))
