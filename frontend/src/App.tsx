import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect } from "react";
import { BrowserRouter } from "react-router-dom";
import { ToastContainer, TopProgressBar } from "./components/ui";
import { DocumentTitle } from "./components/DocumentTitle";
import { AppRouter } from "./router";
import { useAuthStore } from "./store/authStore";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AuthBootstrap() {
  const loadUserFromMe = useAuthStore((state) => state.loadUserFromMe);

  useEffect(() => {
    loadUserFromMe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <TopProgressBar />
        <DocumentTitle />
        <AuthBootstrap />
        <AppRouter />
        <ToastContainer />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
