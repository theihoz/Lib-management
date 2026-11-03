function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object")
    return `{${Object.entries(value)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, item]) => `${JSON.stringify(key)}:${canonical(item)}`)
      .join(",")}}`;
  return JSON.stringify(value) ?? "null";
}

export function createIdempotencyKey() {
  let previous: string | undefined;
  let key: string | undefined;
  return {
    forPayload(payload: unknown) {
      const fingerprint = canonical(payload);
      if (!key || fingerprint !== previous) {
        previous = fingerprint;
        key = crypto.randomUUID();
      }
      return key;
    },
    reset() {
      previous = undefined;
      key = undefined;
    },
  };
}
