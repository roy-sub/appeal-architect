import { AuthGate } from "@/components/workspace/auth-gate";
import { WorkspaceShell } from "@/components/workspace/shell";

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  return (
    <WorkspaceShell>
      <AuthGate>{children}</AuthGate>
    </WorkspaceShell>
  );
}
