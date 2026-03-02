import { useState, useEffect, type KeyboardEvent } from "react";
import { fetchProfile, updateProfile } from "../api";
import { useApi } from "../hooks/useApi";
import { useToast } from "../components/Toast";
import { Loading } from "../components/Loading";

function TagInput({
  label,
  tags,
  onChange,
}: {
  label: string;
  tags: string[];
  onChange: (tags: string[]) => void;
}) {
  const [input, setInput] = useState("");

  const add = () => {
    const val = input.trim();
    if (val && !tags.includes(val)) {
      onChange([...tags, val]);
    }
    setInput("");
  };

  const handleKey = (e: KeyboardEvent) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      add();
    }
    if (e.key === "Backspace" && !input && tags.length) {
      onChange(tags.slice(0, -1));
    }
  };

  return (
    <div className="form-field">
      <label>{label}</label>
      <div className="tag-input-wrap">
        {tags.map((t) => (
          <span key={t} className="tag-pill">
            {t}
            <button
              type="button"
              className="rm-btn"
              onClick={() => onChange(tags.filter((x) => x !== t))}
            >
              &times;
            </button>
          </span>
        ))}
        <input
          className="tag-add-inp"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          onBlur={add}
          placeholder="Type and press Enter..."
        />
      </div>
    </div>
  );
}

export function Profile() {
  const { data: profile, loading, error, refetch } = useApi(() => fetchProfile());
  const { toast } = useToast();

  const [techStack, setTechStack] = useState<string[]>([]);
  const [constraints, setConstraints] = useState<string[]>([]);
  const [interests, setInterests] = useState<string[]>([]);
  const [avoid, setAvoid] = useState<string[]>([]);
  const [timeBudget, setTimeBudget] = useState(10);
  const [revenueGoal, setRevenueGoal] = useState(1000);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (profile) {
      setTechStack(profile.tech_stack || []);
      setConstraints(profile.constraints || []);
      setInterests(profile.interests || []);
      setAvoid(profile.avoid || []);
      setTimeBudget(profile.time_budget_hours_week ?? 10);
      setRevenueGoal(profile.revenue_goal_mrr ?? 1000);
    }
  }, [profile]);

  const handleSave = async () => {
    try {
      setSaving(true);
      await updateProfile({
        tech_stack: techStack,
        constraints,
        interests,
        avoid,
        time_budget_hours_week: timeBudget,
        revenue_goal_mrr: revenueGoal,
      });
      toast("Profile saved", "success");
      refetch();
    } catch (e) {
      toast(e instanceof Error ? e.message : "Save failed", "error");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Loading />;
  if (error) return <div className="err"><h2>Error</h2><p>{error}</p></div>;

  return (
    <div className="profile-form">
      <div className="glass">
        <h2>Builder Profile</h2>
        <p className="td fs mt-s">
          Your profile helps prospector tailor opportunity triage to your skills and goals.
        </p>
      </div>

      <div className="glass">
        <TagInput label="Tech Stack" tags={techStack} onChange={setTechStack} />
        <TagInput label="Constraints" tags={constraints} onChange={setConstraints} />
        <TagInput label="Interests" tags={interests} onChange={setInterests} />
        <TagInput label="Avoid" tags={avoid} onChange={setAvoid} />

        <div className="form-field">
          <label>Time Budget (hours/week)</label>
          <input
            type="number"
            min={1}
            max={80}
            value={timeBudget}
            onChange={(e) => setTimeBudget(Number(e.target.value))}
          />
        </div>

        <div className="form-field">
          <label>Revenue Goal (MRR $)</label>
          <input
            type="number"
            min={0}
            step={100}
            value={revenueGoal}
            onChange={(e) => setRevenueGoal(Number(e.target.value))}
          />
        </div>

        <div className="status-actions mt-m">
          <button disabled={saving} onClick={handleSave} className="active">
            Save Profile
          </button>
        </div>
      </div>
    </div>
  );
}
