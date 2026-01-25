"use client";

import { useState } from "react";
import { addCompetitor, AddCompetitorInput } from "@/lib/api";

interface AddCompetitorModalProps {
  sessionId: string;
  onClose: () => void;
  onAdded: () => void;
}

export function AddCompetitorModal({ sessionId, onClose, onAdded }: AddCompetitorModalProps) {
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [rating, setRating] = useState("");
  const [priceLevel, setPriceLevel] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Name is required");
      return;
    }

    setLoading(true);
    setError(null);

    const data: AddCompetitorInput = {
      session_id: sessionId,
      name: name.trim(),
    };
    if (address.trim()) data.address = address.trim();
    if (rating) {
      const ratingNum = parseFloat(rating);
      if (ratingNum >= 0 && ratingNum <= 5) data.rating = ratingNum;
    }
    if (priceLevel) data.price_level = parseInt(priceLevel);

    try {
      await addCompetitor(data);
      onAdded();
      onClose();
    } catch {
      setError("Failed to add competitor");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative dark-card p-6 w-full max-w-md mx-4">
        <h2 className="text-xl font-semibold text-white mb-4">Add Competitor</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-white/60 text-sm mb-1">Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-white/30"
              placeholder="Competitor name"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-white/60 text-sm mb-1">Address</label>
            <input
              type="text"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-white/30"
              placeholder="123 Main St"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-white/60 text-sm mb-1">Rating (0-5)</label>
              <input
                type="number"
                value={rating}
                onChange={(e) => setRating(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-white/30"
                placeholder="4.5"
                min="0"
                max="5"
                step="0.1"
              />
            </div>

            <div>
              <label className="block text-white/60 text-sm mb-1">Price Level</label>
              <select
                value={priceLevel}
                onChange={(e) => setPriceLevel(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-white/30"
              >
                <option value="">Select</option>
                <option value="1">$ - Budget</option>
                <option value="2">$$ - Moderate</option>
                <option value="3">$$$ - Upscale</option>
                <option value="4">$$$$ - Premium</option>
              </select>
            </div>
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 rounded-lg bg-white/5 text-white hover:bg-white/10 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 rounded-lg bg-white text-black font-medium hover:bg-white/90 transition-colors disabled:opacity-50"
            >
              {loading ? "Adding..." : "Add Competitor"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
