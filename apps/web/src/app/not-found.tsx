import Link from "next/link";
import { AuroraMark } from "@/components/brand/Logo";

export default function NotFound() {
  return (
    <main id="main" className="atmosphere grid min-h-screen place-items-center px-4">
      <div className="max-w-md text-center">
        <AuroraMark size={64} className="mx-auto" />
        <p className="eyebrow mt-6">Page not found</p>
        <h1 className="mt-3 font-display text-3xl font-semibold">This road does not lead anywhere.</h1>
        <p className="mt-3 text-muted">
          The page may have moved, or the district is not part of a published replay.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link href="/" className="btn btn-primary">
            Back to AURORA
          </Link>
          <Link href="/storm/montha_2025/district/13999862/" className="btn btn-ghost">
            Open a control room
          </Link>
        </div>
      </div>
    </main>
  );
}
