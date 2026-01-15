"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { getBusinessProfile, saveBusinessProfile } from "@/lib/api";
import { BusinessProfile } from "@/types";

const BUSINESS_TYPES = [
  { value: "coffee_shop", label: "Coffee Shop" },
  { value: "restaurant", label: "Restaurant" },
  { value: "gym", label: "Gym / Fitness" },
  { value: "retail", label: "Retail Store" },
  { value: "salon", label: "Salon / Spa" },
  { value: "daycare", label: "Daycare" },
  { value: "pet_store", label: "Pet Store" },
];

export default function ProfilePage() {
  const router = useRouter();
  const { user, loading: authLoading, signOut } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [profile, setProfile] = useState<BusinessProfile | null>(null);

  const [formData, setFormData] = useState({
    business_name: "",
    business_type: "",
    location_address: "",
    target_customers: "",
    business_description: "",
  });

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/signin");
    }
  }, [user, authLoading, router]);

  // Load business profile
  useEffect(() => {
    async function loadProfile() {
      if (!user) return;

      try {
        const data = await getBusinessProfile(user.id, "user");
        if (data) {
          setProfile(data);
          setFormData({
            business_name: data.business_name || "",
            business_type: data.business_type || "",
            location_address: data.location_address || "",
            target_customers: data.target_customers || "",
            business_description: data.business_description || "",
          });
        }
      } catch {
        // No profile yet
      } finally {
        setIsFetching(false);
      }
    }

    if (!authLoading && user) {
      loadProfile();
    }
  }, [user, authLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    setError(null);
    setSuccess(null);
    setIsLoading(true);

    try {
      await saveBusinessProfile({
        session_id: user.id,
        user_id: user.id,
        business_name: formData.business_name,
        business_type: formData.business_type,
        location_address: formData.location_address,
        target_customers: formData.target_customers || undefined,
        business_description: formData.business_description || undefined,
      });
      setSuccess("Profile saved successfully!");
    } catch {
      setError("Failed to save profile. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSignOut = async () => {
    await signOut();
    router.push("/");
  };

  if (authLoading || isFetching) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background */}
      <div
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: `url('https://plus.unsplash.com/premium_photo-1664443577580-dd2674e9d359?q=80&w=2071&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D')`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-slate-900/40 via-transparent to-slate-900/60" />

      {/* Header */}
      <header className="glass-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="mx-auto max-w-6xl flex items-center justify-between">
          <Link
            href="/"
            className="text-xl font-bold text-white hover:text-white/80 transition-colors"
          >
            <span className="text-2xl">PHOW</span>
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 pt-24 pb-12 px-6">
        <div className="max-w-xl mx-auto space-y-6">
          {/* User Info Card */}
          <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Account</h2>
            <div className="flex items-center gap-4">
              {user.user_metadata?.avatar_url && (
                <img
                  src={user.user_metadata.avatar_url}
                  alt="Profile"
                  className="w-12 h-12 rounded-full"
                />
              )}
              <div className="flex-1">
                <p className="text-white font-medium">
                  {user.user_metadata?.full_name || "User"}
                </p>
                <p className="text-white/60 text-sm">{user.email}</p>
              </div>
              <button
                onClick={handleSignOut}
                className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20"
              >
                Sign Out
              </button>
            </div>
          </div>

          {/* Business Profile Card */}
          <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8">
            <h1 className="text-2xl font-bold text-white mb-2">Business Profile</h1>
            <p className="text-white/70 mb-6">
              Update your business information to get better insights.
            </p>

            {error && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/40 rounded-lg text-red-200 text-sm">
                {error}
              </div>
            )}

            {success && (
              <div className="mb-4 p-3 bg-green-500/20 border border-green-500/40 rounded-lg text-green-200 text-sm">
                {success}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="business_name" className="block text-sm font-medium text-white/80 mb-1">
                  Business Name *
                </label>
                <input
                  type="text"
                  id="business_name"
                  name="business_name"
                  value={formData.business_name}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-white/30"
                  placeholder="e.g., Joe's Coffee"
                />
              </div>

              <div>
                <label htmlFor="business_type" className="block text-sm font-medium text-white/80 mb-1">
                  Business Type *
                </label>
                <select
                  id="business_type"
                  name="business_type"
                  value={formData.business_type}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-white/30"
                >
                  <option value="" className="bg-slate-800">Select a type...</option>
                  {BUSINESS_TYPES.map((type) => (
                    <option key={type.value} value={type.value} className="bg-slate-800">
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="location_address" className="block text-sm font-medium text-white/80 mb-1">
                  Business Address *
                </label>
                <input
                  type="text"
                  id="location_address"
                  name="location_address"
                  value={formData.location_address}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-white/30"
                  placeholder="e.g., 123 Main St, Austin, TX"
                />
              </div>

              <div>
                <label htmlFor="target_customers" className="block text-sm font-medium text-white/80 mb-1">
                  Target Customers
                </label>
                <input
                  type="text"
                  id="target_customers"
                  name="target_customers"
                  value={formData.target_customers}
                  onChange={handleChange}
                  className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-white/30"
                  placeholder="e.g., Young professionals, students"
                />
              </div>

              <div>
                <label htmlFor="business_description" className="block text-sm font-medium text-white/80 mb-1">
                  Description
                </label>
                <textarea
                  id="business_description"
                  name="business_description"
                  value={formData.business_description}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-white/30 resize-none"
                  placeholder="Brief description of your business..."
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Link
                  href="/"
                  className="flex-1 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-sm font-medium transition-all border border-white/20 text-center"
                >
                  Back to Home
                </Link>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-1 px-4 py-2 rounded-lg bg-white text-slate-900 text-sm font-medium hover:bg-white/90 transition-all disabled:opacity-50"
                >
                  {isLoading ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
