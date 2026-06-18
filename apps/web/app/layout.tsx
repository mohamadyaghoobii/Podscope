import "./styles.css";
import type { Metadata } from "next";
import { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Podscope — Kubernetes manifest review",
  description:
    "Static review for Kubernetes YAML. Catch risky workload, RBAC, exposure, and reliability issues before they reach the cluster.",
  applicationName: "Podscope",
  icons: { icon: "/favicon.svg" }
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
