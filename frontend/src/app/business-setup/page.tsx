"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getSessionId } from "@/lib/session";
import { saveBusinessProfile, getBusinessProfile } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

const BUSINESS_TYPES = [
  { value: "coffee_shop", label: "Coffee Shop" },
  { value: "restaurant", label: "Restaurant" },
  { value: "gym", label: "Gym / Fitness" },
  { value: "retail", label: "Retail Store" },
  { value: "salon", label: "Salon / Spa" },
  { value: "daycare", label: "Daycare" },
  { value: "pet_store", label: "Pet Store" },
];

const LOCATION_COUNTS = ["1", "2-5", "6-10", "11+"];

const GOALS = [
  { id: "rankings", label: "Monitor local rankings", icon: "📍" },
  { id: "competitors", label: "Track competitors", icon: "🏪" },
  { id: "reviews", label: "Manage reviews", icon: "⭐" },
  { id: "insights", label: "Get market insights", icon: "📊" },
];

const inputClass =
  "w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50";

export default function BusinessSetupPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState(0);

  const [formData, setFormData] = useState({
    business_name: "",
    business_type: "",
    location_address: "",
    target_customers: "",
    business_description: "",
    num_locations: "1",
    goals: [] as string[],
  });

  useEffect(() => {
    async function loadProfile() {
      if (authLoading) return;
      try {
        let profile = null;
        if (user) {
          profile = await getBusinessProfile(user.id, "user");
        }
        if (!profile) {
          const sessionId = getSessionId();
          if (sessionId) {
            profile = await getBusinessProfile(sessionId, "session");
          }
        }
        if (profile) {
          setFormData((prev) => ({
            ...prev,
            business_name: profile.business_name || "",
            business_type: profile.business_type || "",
            location_address: profile.location_address || "",
            target_customers: profile.target_customers || "",
            business_description: profile.business_description || "",
          }));
        }
      } catch {
        // Ignore
      } finally {
        setIsFetching(false);
      }
    }
    loadProfile();
  }, [user, authLoading]);

  const handleSubmit = async () => {
    setError(null);
    setIsLoading(true);
    try {
      const sessionId = getSessionId();
      await saveBusinessProfile({
        session_id: user?.id || sessionId,
        user_id: user?.id,
        business_name: formData.business_name,
        business_type: formData.business_type,
        location_address: formData.location_address,
        target_customers: formData.target_customers || undefined,
        business_description: formData.business_description || undefined,
      });
      router.push("/dashboard");
    } catch {
      setError("Failed to save profile. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const toggleGoal = (goalId: string) => {
    setFormData((prev) => ({
      ...prev,
      goals: prev.goals.includes(goalId)
        ? prev.goals.filter((g) => g !== goalId)
        : [...prev.goals, goalId],
    }));
  };

  const canAdvance =
    step === 0
      ? formData.business_name && formData.business_type && formData.location_address
      : true;

  const handleNext = () => {
    if (step < 2) setStep(step + 1);
    else handleSubmit();
  };

  if (authLoading || isFetching) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0a0a0a]">
        <div className="text-white/50">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] relative overflow-hidden">
      <div className="fixed inset-0 grid-pattern pointer-events-none" />

      <header className="dark-header fixed top-0 left-0 right-0 z-50 px-6 py-4">
        <div className="mx-auto max-w-6xl flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-white hover:text-white/80 transition-colors tracking-tight">
            PHOW
          </Link>
        </div>
      </header>

      <main className="relative z-10 min-h-screen flex items-center justify-center px-6 pt-24 pb-12">
        <div className="max-w-xl w-full animate-fade-in-up">
          <div className="dark-card p-8">
            {/* Progress Bar */}
            <div className="flex gap-2 mb-6">
              {["Business Info", "Details", "Goals"].map((label, i) => (
                <div key={label} className="flex-1">
                  <div
                    className={`h-1 rounded-full transition-colors ${
                      i <= step ? "bg-blue-500" : "bg-white/10"
                    }`}
                  />
                  <p className={`text-xs mt-1 ${i <= step ? "text-white/70" : "text-white/30"}`}>
                    {label}
                  </p>
                </div>
              ))}
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* Step 1: Business Info */}
            {step === 0 && (
              <div className="space-y-5">
                <h2 className="text-xl font-bold text-white">Business Info</h2>
                <p className="text-white/50 text-sm">Tell us the basics about your business.</p>

                <div>
                  <label htmlFor="business_name" className="block text-sm font-medium text-white/70 mb-1">
                    Business Name *
                  </label>
                  <input
                    type="text"
                    id="business_name"
                    name="business_name"
                    value={formData.business_name}
                    onChange={handleChange}
                    required
                    className={inputClass}
                    placeholder="e.g., Joe's Coffee"
                  />
                </div>

                <div>
                  <label htmlFor="business_type" className="block text-sm font-medium text-white/70 mb-1">
                    Business Type *
                  </label>
                  <select
                    id="business_type"
                    name="business_type"
                    value={formData.business_type}
                    onChange={handleChange}
                    required
                    className={inputClass}
                  >
                    <option value="" className="bg-[#111]">Select a type...</option>
                    {BUSINESS_TYPES.map((type) => (
                      <option key={type.value} value={type.value} className="bg-[#111]">
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="location_address" className="block text-sm font-medium text-white/70 mb-1">
                    Business Address *
                  </label>
                  <input
                    type="text"
                    id="location_address"
                    name="location_address"
                    value={formData.location_address}
                    onChange={handleChange}
                    required
                    className={inputClass}
                    placeholder="e.g., 123 Main St, Austin, TX"
                  />
                </div>
              </div>
            )}

            {/* Step 2: Details */}
            {step === 1 && (
              <div className="space-y-5">
                <h2 className="text-xl font-bold text-white">Business Details</h2>
                <p className="text-white/50 text-sm">Help us understand your business better.</p>

                <div>
                  <label htmlFor="business_description" className="block text-sm font-medium text-white/70 mb-1">
                    Description
                  </label>
                  <textarea
                    id="business_description"
                    name="business_description"
                    value={formData.business_description}
                    onChange={handleChange}
                    rows={3}
                    className={`${inputClass} resize-none`}
                    placeholder="Brief description of your business..."
                  />
                </div>

                <div>
                  <label htmlFor="target_customers" className="block text-sm font-medium text-white/70 mb-1">
                    Target Customers
                  </label>
                  <input
                    type="text"
                    id="target_customers"
                    name="target_customers"
                    value={formData.target_customers}
                    onChange={handleChange}
                    className={inputClass}
                    placeholder="e.g., Young professionals, students"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">
                    Number of Locations
                  </label>
                  <div className="flex gap-2">
                    {LOCATION_COUNTS.map((count) => (
                      <button
                        key={count}
                        type="button"
                        onClick={() => setFormData((prev) => ({ ...prev, num_locations: count }))}
                        className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors border ${
                          formData.num_locations === count
                            ? "bg-blue-500/20 border-blue-500/50 text-blue-400"
                            : "bg-white/5 border-white/10 text-white/50 hover:bg-white/10"
                        }`}
                      >
                        {count}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Goals */}
            {step === 2 && (
              <div className="space-y-5">
                <h2 className="text-xl font-bold text-white">Your Goals</h2>
                <p className="text-white/50 text-sm">What would you like to achieve with PHOW?</p>

                <div className="grid grid-cols-2 gap-3">
                  {GOALS.map((goal) => {
                    const selected = formData.goals.includes(goal.id);
                    return (
                      <button
                        key={goal.id}
                        type="button"
                        onClick={() => toggleGoal(goal.id)}
                        className={`p-4 rounded-lg text-left transition-colors border ${
                          selected
                            ? "bg-blue-500/20 border-blue-500/50"
                            : "bg-white/5 border-white/10 hover:bg-white/10"
                        }`}
                      >
                        <span className="text-2xl block mb-2">{goal.icon}</span>
                        <span className={`text-sm font-medium ${selected ? "text-blue-400" : "text-white/70"}`}>
                          {goal.label}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Navigation */}
            <div className="flex gap-3 pt-6">
              {step > 0 ? (
                <button
                  type="button"
                  onClick={() => setStep(step - 1)}
                  className="flex-1 px-4 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 text-white text-sm font-medium transition-all border border-white/10"
                >
                  Back
                </button>
              ) : (
                <Link
                  href="/"
                  className="flex-1 px-4 py-2.5 rounded-lg bg-white/5 hover:bg-white/10 text-white text-sm font-medium transition-all border border-white/10 text-center"
                >
                  Cancel
                </Link>
              )}
              <button
                type="button"
                onClick={handleNext}
                disabled={!canAdvance || isLoading}
                className="flex-1 px-4 py-2.5 rounded-lg bg-white text-black text-sm font-medium hover:bg-white/90 transition-all disabled:opacity-50"
              >
                {step < 2 ? "Next" : isLoading ? "Saving..." : "Save Profile"}
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
