/** @type {import('next').NextConfig} */
const nextConfig = {
  typedRoutes: false,
  // Revalidate on demand via Vercel deploy hook; static pages otherwise.
};

export default nextConfig;
