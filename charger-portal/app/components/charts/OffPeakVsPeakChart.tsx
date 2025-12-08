'use client'

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import type { SessionSplit } from '@/lib/types/dashboard'

interface OffPeakVsPeakChartProps {
  data: SessionSplit[]
}

const COLORS = {
  'off-peak': '#10b981', // green
  peak: '#ef4444', // red
}

export function OffPeakVsPeakChart({ data }: OffPeakVsPeakChartProps) {
  const total = data.reduce((sum, item) => sum + item.count, 0)
  
  const chartData = data.map((item) => ({
    name: item.type === 'off-peak' ? 'Off-peak Sessions' : 'Peak Sessions',
    value: item.count,
    percentage: ((item.count / total) * 100).toFixed(0),
  }))

  return (
    <div className="w-full h-[300px] sm:h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percentage }) => `${name}: ${percentage}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.name.includes('Off-peak') ? COLORS['off-peak'] : COLORS.peak}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            formatter={(value: number) => [value, 'Sessions']}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value) => {
              const item = chartData.find((d) => d.name === value)
              return `${value} (${item?.percentage}%)`
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

