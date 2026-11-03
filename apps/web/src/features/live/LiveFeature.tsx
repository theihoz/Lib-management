import { lazy, Suspense } from "react";
import type { ScreenDefinition } from "../types";
import { LoadingSkeleton } from "./common";

const Catalog = lazy(() => import("./Catalog"));
const Readers = lazy(() => import("./Readers"));
const Circulation = lazy(() => import("./Circulation"));
const Records = lazy(() => import("./Records"));
const Finance = lazy(() => import("./Finance"));
const Reports = lazy(() => import("./Reports"));
const Policies = lazy(() => import("./Policies"));
export default function LiveFeature({ screen }: { screen: ScreenDefinition }) {
  const View =
    screen.group === "02"
      ? Catalog
      : screen.group === "03"
        ? Readers
        : ["04", "05", "06"].includes(screen.group)
          ? Circulation
          : screen.group === "07"
            ? Finance
            : ["FE09.02", "FE09.03", "FE09.04"].includes(screen.id)
            ? Reports
            : ["FE09.05", "FE09.06"].includes(screen.id)
              ? Policies
              : Records;
  return (
    <Suspense fallback={<LoadingSkeleton books={screen.kind === "catalog"} />}>
      <View screen={screen} />
    </Suspense>
  );
}
