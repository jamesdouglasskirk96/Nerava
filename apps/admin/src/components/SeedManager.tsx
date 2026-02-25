import { useState, useEffect, useCallback } from 'react';
import { Database, Loader2, CheckCircle, XCircle, MapPin, Store, Link2 } from 'lucide-react';
import { startChargerSeed, startMerchantSeed, getSeedStatus, getSeedStats } from '../services/api';

interface SeedJob {
  type: string;
  status: string;
  started_at: string;
  started_by?: number;
  progress: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error: string | null;
  completed_at?: string;
}

interface SeedStats {
  charger_count: number;
  merchant_count: number;
  junction_count: number;
  last_charger_update: string | null;
  last_merchant_update: string | null;
}

const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
  'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
  'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
  'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC',
];

export function SeedManager() {
  const [stats, setStats] = useState<SeedStats | null>(null);
  const [jobs, setJobs] = useState<Record<string, SeedJob>>({});
  const [selectedStates, setSelectedStates] = useState<string[]>([]);
  const [maxCells, setMaxCells] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshStats = useCallback(async () => {
    try {
      const data = await getSeedStats();
      setStats(data);
    } catch {
      // stats endpoint may not be available yet
    }
  }, []);

  const refreshJobs = useCallback(async () => {
    try {
      const data = await getSeedStatus();
      setJobs((data.jobs || {}) as Record<string, SeedJob>);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    refreshStats();
    refreshJobs();
  }, [refreshStats, refreshJobs]);

  // Poll for job updates when any job is running
  useEffect(() => {
    const hasRunning = Object.values(jobs).some(j => j.status === 'running' || j.status === 'starting');
    if (!hasRunning) return;

    const interval = setInterval(() => {
      refreshJobs();
      refreshStats();
    }, 3000);
    return () => clearInterval(interval);
  }, [jobs, refreshJobs, refreshStats]);

  const handleSeedChargers = async () => {
    setLoading(true);
    setError(null);
    try {
      const states = selectedStates.length > 0 ? selectedStates : undefined;
      await startChargerSeed(states);
      await refreshJobs();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to start charger seed');
    } finally {
      setLoading(false);
    }
  };

  const handleSeedMerchants = async () => {
    setLoading(true);
    setError(null);
    try {
      const cells = maxCells ? parseInt(maxCells) : undefined;
      await startMerchantSeed(cells);
      await refreshJobs();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to start merchant seed');
    } finally {
      setLoading(false);
    }
  };

  const toggleState = (state: string) => {
    setSelectedStates(prev =>
      prev.includes(state) ? prev.filter(s => s !== state) : [...prev, state]
    );
  };

  const latestChargerJob = Object.entries(jobs)
    .filter(([, j]) => j.type === 'chargers')
    .sort(([, a], [, b]) => b.started_at.localeCompare(a.started_at))[0];

  const latestMerchantJob = Object.entries(jobs)
    .filter(([, j]) => j.type === 'merchants')
    .sort(([, a], [, b]) => b.started_at.localeCompare(a.started_at))[0];

  return (
    <div className="p-8 max-w-6xl">
      <div className="flex items-center gap-3 mb-8">
        <Database className="w-6 h-6 text-neutral-700" />
        <h1 className="text-2xl font-semibold text-neutral-900">Data Seeding</h1>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <StatCard
          icon={<MapPin className="w-5 h-5 text-blue-600" />}
          label="Chargers"
          value={stats?.charger_count ?? '—'}
          subtitle={stats?.last_charger_update ? `Updated ${new Date(stats.last_charger_update).toLocaleDateString()}` : 'Not seeded yet'}
        />
        <StatCard
          icon={<Store className="w-5 h-5 text-green-600" />}
          label="Merchants"
          value={stats?.merchant_count ?? '—'}
          subtitle={stats?.last_merchant_update ? `Updated ${new Date(stats.last_merchant_update).toLocaleDateString()}` : 'Not seeded yet'}
        />
        <StatCard
          icon={<Link2 className="w-5 h-5 text-purple-600" />}
          label="Charger-Merchant Links"
          value={stats?.junction_count ?? '—'}
          subtitle="Walkable connections"
        />
      </div>

      {/* Seed Chargers Section */}
      <div className="bg-white rounded-lg border border-neutral-200 p-6 mb-6">
        <h2 className="text-lg font-medium text-neutral-900 mb-2">Seed EV Chargers</h2>
        <p className="text-sm text-neutral-500 mb-4">
          Fetch all US public EV charging stations from NREL AFDC (free API). ~70K stations across 50 states + DC.
        </p>

        {/* State filter */}
        <div className="mb-4">
          <label className="text-sm font-medium text-neutral-700 block mb-2">
            Filter by states (optional — leave empty for all states):
          </label>
          <div className="flex flex-wrap gap-1.5">
            {US_STATES.map(state => (
              <button
                key={state}
                onClick={() => toggleState(state)}
                className={`px-2 py-1 text-xs rounded border transition-colors ${
                  selectedStates.includes(state)
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-neutral-600 border-neutral-300 hover:border-blue-400'
                }`}
              >
                {state}
              </button>
            ))}
          </div>
          {selectedStates.length > 0 && (
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs text-neutral-500">{selectedStates.length} states selected</span>
              <button onClick={() => setSelectedStates([])} className="text-xs text-blue-600 hover:underline">Clear</button>
            </div>
          )}
        </div>

        <button
          onClick={handleSeedChargers}
          disabled={loading || (latestChargerJob && latestChargerJob[1].status === 'running')}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Starting...' : 'Seed Chargers'}
        </button>

        {latestChargerJob && <JobStatus jobId={latestChargerJob[0]} job={latestChargerJob[1]} />}
      </div>

      {/* Seed Merchants Section */}
      <div className="bg-white rounded-lg border border-neutral-200 p-6">
        <h2 className="text-lg font-medium text-neutral-900 mb-2">Map Nearby Merchants</h2>
        <p className="text-sm text-neutral-500 mb-4">
          Discover walkable merchants near chargers using OpenStreetMap Overpass API (100% free).
          Groups chargers into grid cells and queries POIs within 800m walking distance.
        </p>

        <div className="mb-4">
          <label className="text-sm font-medium text-neutral-700 block mb-1">
            Max cells to process (optional — leave empty for all):
          </label>
          <input
            type="number"
            value={maxCells}
            onChange={e => setMaxCells(e.target.value)}
            placeholder="e.g., 100"
            className="w-40 px-3 py-1.5 border border-neutral-300 rounded-md text-sm"
          />
        </div>

        <button
          onClick={handleSeedMerchants}
          disabled={loading || (latestMerchantJob && latestMerchantJob[1].status === 'running') || !stats?.charger_count}
          className="px-4 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Starting...' : 'Map Merchants'}
        </button>
        {!stats?.charger_count && (
          <p className="mt-2 text-xs text-amber-600">Seed chargers first before mapping merchants.</p>
        )}

        {latestMerchantJob && <JobStatus jobId={latestMerchantJob[0]} job={latestMerchantJob[1]} />}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, subtitle }: { icon: React.ReactNode; label: string; value: number | string; subtitle: string }) {
  return (
    <div className="bg-white rounded-lg border border-neutral-200 p-5">
      <div className="flex items-center gap-2 mb-2">
        {icon}
        <span className="text-sm font-medium text-neutral-600">{label}</span>
      </div>
      <div className="text-3xl font-semibold text-neutral-900">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      <div className="text-xs text-neutral-400 mt-1">{subtitle}</div>
    </div>
  );
}

function JobStatus({ jobId, job }: { jobId: string; job: SeedJob }) {
  const isRunning = job.status === 'running' || job.status === 'starting';
  const isComplete = job.status === 'completed';
  const isFailed = job.status === 'failed';

  return (
    <div className={`mt-4 p-4 rounded-lg border ${
      isRunning ? 'bg-blue-50 border-blue-200' :
      isComplete ? 'bg-green-50 border-green-200' :
      isFailed ? 'bg-red-50 border-red-200' :
      'bg-neutral-50 border-neutral-200'
    }`}>
      <div className="flex items-center gap-2 mb-1">
        {isRunning && <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />}
        {isComplete && <CheckCircle className="w-4 h-4 text-green-600" />}
        {isFailed && <XCircle className="w-4 h-4 text-red-600" />}
        <span className="text-sm font-medium">
          {isRunning ? 'Running' : isComplete ? 'Completed' : isFailed ? 'Failed' : job.status}
        </span>
        <span className="text-xs text-neutral-400">({jobId})</span>
      </div>

      {/* Progress */}
      {isRunning && job.progress && Object.keys(job.progress).length > 0 && (
        <div className="text-xs text-neutral-600 mt-1">
          {job.type === 'chargers' && (
            <>Processing state: {(job.progress as Record<string, unknown>).current_state}, fetched: {((job.progress as Record<string, unknown>).total_fetched as number || 0).toLocaleString()}</>
          )}
          {job.type === 'merchants' && (
            <>Cells: {(job.progress as Record<string, unknown>).cells_done}/{(job.progress as Record<string, unknown>).total_cells}</>
          )}
        </div>
      )}

      {/* Result */}
      {isComplete && job.result && (
        <div className="text-xs text-neutral-600 mt-1 space-y-0.5">
          {job.type === 'chargers' && (
            <>
              <div>Inserted: {((job.result as Record<string, unknown>).inserted as number || 0).toLocaleString()}, Updated: {((job.result as Record<string, unknown>).updated as number || 0).toLocaleString()}</div>
              <div>Total fetched: {((job.result as Record<string, unknown>).total_fetched as number || 0).toLocaleString()}, States: {(job.result as Record<string, unknown>).states_processed as number || 0}</div>
            </>
          )}
          {job.type === 'merchants' && (
            <>
              <div>Merchants created: {((job.result as Record<string, unknown>).merchants_created as number || 0).toLocaleString()}, Junctions: {((job.result as Record<string, unknown>).junctions_created as number || 0).toLocaleString()}</div>
              <div>Corporate skipped: {((job.result as Record<string, unknown>).corporate_skipped as number || 0).toLocaleString()}, Cells: {(job.result as Record<string, unknown>).cells_processed as number || 0}</div>
            </>
          )}
        </div>
      )}

      {/* Error */}
      {isFailed && job.error && (
        <div className="text-xs text-red-600 mt-1">{job.error}</div>
      )}

      <div className="text-xs text-neutral-400 mt-2">
        Started: {new Date(job.started_at).toLocaleString()}
        {job.completed_at && <> | Completed: {new Date(job.completed_at).toLocaleString()}</>}
      </div>
    </div>
  );
}
