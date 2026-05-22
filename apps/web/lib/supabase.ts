import { createClient, SupabaseClient } from "@supabase/supabase-js";

let _client: SupabaseClient | null = null;

function build(): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) {
    // Build-time / missing config: return a stub whose every call throws.
    // Page-level catch() will swallow it and render an empty UI.
    return new Proxy({} as SupabaseClient, {
      get() {
        throw new Error("Supabase env not configured");
      },
    });
  }
  return createClient(url, key, { auth: { persistSession: false } });
}

export const supabase: SupabaseClient = new Proxy({} as SupabaseClient, {
  get(_t, prop) {
    if (!_client) _client = build();
    return (_client as any)[prop];
  },
});
