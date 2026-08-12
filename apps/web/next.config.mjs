/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Standalone output keeps the production image small and self-hostable/air-gapped.
  output: "standalone",
};

export default nextConfig;
