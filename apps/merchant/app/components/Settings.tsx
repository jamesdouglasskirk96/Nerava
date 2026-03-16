import { useState, useEffect } from 'react';
import { Save, Loader2 } from 'lucide-react';
import { fetchAPI } from '../services/api';

interface ProfileData {
  name: string;
  description: string;
  photo_url: string;
  website: string;
  hours_text: string;
  perk_label: string;
  custom_perk_cents: number | '';
}

export function Settings() {
  const [form, setForm] = useState<ProfileData>({
    name: '',
    description: '',
    photo_url: '',
    website: '',
    hours_text: '',
    perk_label: '',
    custom_perk_cents: '',
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load current merchant data
    fetchAPI<{ merchant: Record<string, any> }>('/v1/merchants/me')
      .then((data) => {
        const m = data.merchant;
        setForm({
          name: m.name || '',
          description: m.description || '',
          photo_url: m.photo_url || '',
          website: m.website || '',
          hours_text: m.hours_text || '',
          perk_label: m.perk_label || '',
          custom_perk_cents: m.custom_perk_cents || '',
        });
      })
      .catch(() => {
        // Merchant might not have all fields yet
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await fetchAPI('/v1/merchants/me/profile', {
        method: 'PUT',
        body: JSON.stringify({
          ...form,
          custom_perk_cents: form.custom_perk_cents === '' ? null : Number(form.custom_perk_cents),
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-neutral-400" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-neutral-900">Settings</h2>
        <p className="text-sm text-neutral-500 mt-1">Manage your business profile and EV reward</p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {saved && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm">
          Profile saved successfully.
        </div>
      )}

      <div className="bg-white rounded-xl border border-neutral-200 p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Business Name</label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Description</label>
          <textarea
            rows={3}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Tell EV drivers about your business..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Photo URL</label>
          <input
            type="url"
            value={form.photo_url}
            onChange={(e) => setForm({ ...form, photo_url: e.target.value })}
            className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="https://..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Website</label>
          <input
            type="url"
            value={form.website}
            onChange={(e) => setForm({ ...form, website: e.target.value })}
            className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="https://yourbusiness.com"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">Hours</label>
          <input
            type="text"
            value={form.hours_text}
            onChange={(e) => setForm({ ...form, hours_text: e.target.value })}
            className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Mon-Fri 7am-7pm, Sat-Sun 8am-5pm"
          />
        </div>

        <div className="border-t border-neutral-200 pt-5">
          <h3 className="text-sm font-semibold text-neutral-900 mb-3">EV Reward</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">Perk Label</label>
              <input
                type="text"
                value={form.perk_label}
                onChange={(e) => setForm({ ...form, perk_label: e.target.value })}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="$3 off any order"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">Perk Value (cents)</label>
              <input
                type="number"
                value={form.custom_perk_cents}
                onChange={(e) =>
                  setForm({ ...form, custom_perk_cents: e.target.value === '' ? '' : Number(e.target.value) })
                }
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="300"
              />
            </div>
          </div>
        </div>

        <div className="pt-2">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 bg-neutral-900 text-white px-6 py-2.5 rounded-lg hover:bg-neutral-800 transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
