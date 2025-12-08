import { DashboardData, NOVA_PER_USD } from '../types/dashboard'

// Helper to generate dates
const getDateString = (daysAgo: number): string => {
  const date = new Date()
  date.setDate(date.getDate() - daysAgo)
  return date.toISOString().split('T')[0]
}

const getDateTimeString = (daysAgo: number, hours: number = 0): string => {
  const date = new Date()
  date.setDate(date.getDate() - daysAgo)
  date.setHours(hours, 0, 0, 0)
  return date.toISOString()
}

// Generate realistic daily savings data (30 days)
const generateDailySavings = (baseSavings: number, variance: number) => {
  const data = []
  for (let i = 29; i >= 0; i--) {
    // Weekends tend to have lower savings
    const date = new Date()
    date.setDate(date.getDate() - i)
    const dayOfWeek = date.getDay()
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6
    const multiplier = isWeekend ? 0.7 : 1.0
    const randomVariance = (Math.random() - 0.5) * variance
    const savings = Math.max(0, baseSavings * multiplier + randomVariance)
    data.push({
      date: getDateString(i),
      savingsUsd: Math.round(savings * 100) / 100,
    })
  }
  return data
}

// Property 1: The Standard at Domain Northside (high performance)
const property1Data: DashboardData = {
  property: {
    id: 'standard-domain',
    name: 'The Standard at Domain Northside',
  },
  kpis: {
    monthlySavings: 1240,
    novaPurchased: 12500,
    rewardsIssued: 780,
    activeDrivers: 42,
  },
  dailySavings: generateDailySavings(45, 15),
  sessionSplit: [
    { type: 'off-peak', count: 136 },
    { type: 'peak', count: 64 },
  ],
  sessions: [
    {
      id: 's1',
      driverName: 'Alex R.',
      dateTime: getDateTimeString(0, 1),
      sessionType: 'off-peak',
      energyKwh: 45.2,
      estimatedCost: 8.50,
      novaAwarded: 250,
    },
    {
      id: 's2',
      driverName: 'Taylor M.',
      dateTime: getDateTimeString(0, 14),
      sessionType: 'peak',
      energyKwh: 38.7,
      estimatedCost: 12.30,
      novaAwarded: 0,
    },
    {
      id: 's3',
      driverName: 'Jordan K.',
      dateTime: getDateTimeString(1, 2),
      sessionType: 'off-peak',
      energyKwh: 52.1,
      estimatedCost: 9.80,
      novaAwarded: 300,
    },
    {
      id: 's4',
      driverName: 'Casey L.',
      dateTime: getDateTimeString(1, 15),
      sessionType: 'peak',
      energyKwh: 41.3,
      estimatedCost: 13.10,
      novaAwarded: 0,
    },
    {
      id: 's5',
      driverName: 'Morgan P.',
      dateTime: getDateTimeString(2, 0),
      sessionType: 'off-peak',
      energyKwh: 48.9,
      estimatedCost: 9.20,
      novaAwarded: 280,
    },
    {
      id: 's6',
      driverName: 'Riley S.',
      dateTime: getDateTimeString(2, 16),
      sessionType: 'peak',
      energyKwh: 35.6,
      estimatedCost: 11.30,
      novaAwarded: 0,
    },
    {
      id: 's7',
      driverName: 'Alex R.',
      dateTime: getDateTimeString(3, 1),
      sessionType: 'off-peak',
      energyKwh: 46.8,
      estimatedCost: 8.80,
      novaAwarded: 260,
    },
    {
      id: 's8',
      driverName: 'Sam T.',
      dateTime: getDateTimeString(3, 17),
      sessionType: 'peak',
      energyKwh: 39.4,
      estimatedCost: 12.50,
      novaAwarded: 0,
    },
    {
      id: 's9',
      driverName: 'Taylor M.',
      dateTime: getDateTimeString(4, 3),
      sessionType: 'off-peak',
      energyKwh: 50.2,
      estimatedCost: 9.40,
      novaAwarded: 290,
    },
    {
      id: 's10',
      driverName: 'Jordan K.',
      dateTime: getDateTimeString(4, 18),
      sessionType: 'peak',
      energyKwh: 37.1,
      estimatedCost: 11.80,
      novaAwarded: 0,
    },
    {
      id: 's11',
      driverName: 'Casey L.',
      dateTime: getDateTimeString(5, 0),
      sessionType: 'off-peak',
      energyKwh: 44.5,
      estimatedCost: 8.40,
      novaAwarded: 240,
    },
    {
      id: 's12',
      driverName: 'Morgan P.',
      dateTime: getDateTimeString(5, 19),
      sessionType: 'peak',
      energyKwh: 40.8,
      estimatedCost: 12.90,
      novaAwarded: 0,
    },
    {
      id: 's13',
      driverName: 'Riley S.',
      dateTime: getDateTimeString(6, 2),
      sessionType: 'off-peak',
      energyKwh: 47.3,
      estimatedCost: 8.90,
      novaAwarded: 270,
    },
    {
      id: 's14',
      driverName: 'Alex R.',
      dateTime: getDateTimeString(7, 1),
      sessionType: 'off-peak',
      energyKwh: 49.6,
      estimatedCost: 9.30,
      novaAwarded: 285,
    },
    {
      id: 's15',
      driverName: 'Sam T.',
      dateTime: getDateTimeString(7, 20),
      sessionType: 'peak',
      energyKwh: 36.2,
      estimatedCost: 11.50,
      novaAwarded: 0,
    },
  ],
  activity: [
    {
      id: 'a1',
      timestamp: getDateTimeString(0, 1),
      type: 'SAVINGS',
      description: 'Awarded 250 Nova to Alex R. for off-peak charging at 1:00 AM.',
    },
    {
      id: 'a2',
      timestamp: getDateTimeString(0, 10),
      type: 'REWARD',
      description: 'Converted 1,000 Nova into Starbucks digital cards.',
    },
    {
      id: 'a3',
      timestamp: getDateTimeString(1, 8),
      type: 'TOP_UP',
      description: 'Auto top-up executed: purchased 5,000 Nova ($500).',
    },
    {
      id: 'a4',
      timestamp: getDateTimeString(2, 2),
      type: 'SAVINGS',
      description: 'Awarded 300 Nova to Jordan K. for off-peak charging at 2:00 AM.',
    },
    {
      id: 'a5',
      timestamp: getDateTimeString(3, 14),
      type: 'REWARD',
      description: 'Converted 2,500 Nova into Amazon gift cards.',
    },
    {
      id: 'a6',
      timestamp: getDateTimeString(4, 3),
      type: 'SAVINGS',
      description: 'Awarded 290 Nova to Taylor M. for off-peak charging at 3:00 AM.',
    },
    {
      id: 'a7',
      timestamp: getDateTimeString(5, 9),
      type: 'PURCHASE',
      description: 'Purchased 3,000 Nova ($300) - Monthly budget replenishment.',
    },
    {
      id: 'a8',
      timestamp: getDateTimeString(6, 2),
      type: 'SAVINGS',
      description: 'Awarded 270 Nova to Riley S. for off-peak charging at 2:00 AM.',
    },
  ],
  novaBudget: {
    total: 15000,
    spent: 9200,
    remaining: 5800,
    totalUsd: 1500,
    projectedRunoutDate: getDateString(-18), // 18 days from now based on burn rate
  },
  autoTopUpConfig: {
    enabled: true,
    threshold: 3000,
    topUpAmountUsd: 500,
    topUpAmountNova: 5000,
    frequency: 'No limit',
  },
}

// Property 2: Bridge at the Kenzie (medium performance)
const property2Data: DashboardData = {
  property: {
    id: 'bridge-kenzie',
    name: 'Bridge at the Kenzie',
  },
  kpis: {
    monthlySavings: 890,
    novaPurchased: 8500,
    rewardsIssued: 520,
    activeDrivers: 28,
  },
  dailySavings: generateDailySavings(32, 12),
  sessionSplit: [
    { type: 'off-peak', count: 95 },
    { type: 'peak', count: 55 },
  ],
  sessions: [
    {
      id: 's21',
      driverName: 'Jamie W.',
      dateTime: getDateTimeString(0, 2),
      sessionType: 'off-peak',
      energyKwh: 42.3,
      estimatedCost: 7.90,
      novaAwarded: 220,
    },
    {
      id: 's22',
      driverName: 'Drew H.',
      dateTime: getDateTimeString(0, 13),
      sessionType: 'peak',
      energyKwh: 36.8,
      estimatedCost: 11.70,
      novaAwarded: 0,
    },
    {
      id: 's23',
      driverName: 'Quinn B.',
      dateTime: getDateTimeString(1, 1),
      sessionType: 'off-peak',
      energyKwh: 45.7,
      estimatedCost: 8.60,
      novaAwarded: 250,
    },
    {
      id: 's24',
      driverName: 'Avery C.',
      dateTime: getDateTimeString(1, 14),
      sessionType: 'peak',
      energyKwh: 34.2,
      estimatedCost: 10.90,
      novaAwarded: 0,
    },
    {
      id: 's25',
      driverName: 'Jamie W.',
      dateTime: getDateTimeString(2, 0),
      sessionType: 'off-peak',
      energyKwh: 43.1,
      estimatedCost: 8.10,
      novaAwarded: 230,
    },
    {
      id: 's26',
      driverName: 'Drew H.',
      dateTime: getDateTimeString(2, 15),
      sessionType: 'peak',
      energyKwh: 35.9,
      estimatedCost: 11.40,
      novaAwarded: 0,
    },
    {
      id: 's27',
      driverName: 'Quinn B.',
      dateTime: getDateTimeString(3, 2),
      sessionType: 'off-peak',
      energyKwh: 44.8,
      estimatedCost: 8.40,
      novaAwarded: 240,
    },
    {
      id: 's28',
      driverName: 'Avery C.',
      dateTime: getDateTimeString(3, 16),
      sessionType: 'peak',
      energyKwh: 33.5,
      estimatedCost: 10.60,
      novaAwarded: 0,
    },
    {
      id: 's29',
      driverName: 'Jamie W.',
      dateTime: getDateTimeString(4, 1),
      sessionType: 'off-peak',
      energyKwh: 46.2,
      estimatedCost: 8.70,
      novaAwarded: 260,
    },
    {
      id: 's30',
      driverName: 'Drew H.',
      dateTime: getDateTimeString(4, 17),
      sessionType: 'peak',
      energyKwh: 37.4,
      estimatedCost: 11.90,
      novaAwarded: 0,
    },
    {
      id: 's31',
      driverName: 'Quinn B.',
      dateTime: getDateTimeString(5, 0),
      sessionType: 'off-peak',
      energyKwh: 41.9,
      estimatedCost: 7.90,
      novaAwarded: 210,
    },
    {
      id: 's32',
      driverName: 'Avery C.',
      dateTime: getDateTimeString(5, 18),
      sessionType: 'peak',
      energyKwh: 36.1,
      estimatedCost: 11.50,
      novaAwarded: 0,
    },
    {
      id: 's33',
      driverName: 'Jamie W.',
      dateTime: getDateTimeString(6, 3),
      sessionType: 'off-peak',
      energyKwh: 45.5,
      estimatedCost: 8.60,
      novaAwarded: 250,
    },
    {
      id: 's34',
      driverName: 'Drew H.',
      dateTime: getDateTimeString(7, 1),
      sessionType: 'off-peak',
      energyKwh: 44.1,
      estimatedCost: 8.30,
      novaAwarded: 240,
    },
    {
      id: 's35',
      driverName: 'Quinn B.',
      dateTime: getDateTimeString(7, 19),
      sessionType: 'peak',
      energyKwh: 35.7,
      estimatedCost: 11.30,
      novaAwarded: 0,
    },
  ],
  activity: [
    {
      id: 'a21',
      timestamp: getDateTimeString(0, 2),
      type: 'SAVINGS',
      description: 'Awarded 220 Nova to Jamie W. for off-peak charging at 2:00 AM.',
    },
    {
      id: 'a22',
      timestamp: getDateTimeString(0, 11),
      type: 'REWARD',
      description: 'Converted 800 Nova into Target gift cards.',
    },
    {
      id: 'a23',
      timestamp: getDateTimeString(1, 9),
      type: 'TOP_UP',
      description: 'Auto top-up executed: purchased 3,000 Nova ($300).',
    },
    {
      id: 'a24',
      timestamp: getDateTimeString(2, 1),
      type: 'SAVINGS',
      description: 'Awarded 230 Nova to Jamie W. for off-peak charging at 1:00 AM.',
    },
    {
      id: 'a25',
      timestamp: getDateTimeString(3, 15),
      type: 'REWARD',
      description: 'Converted 1,500 Nova into Starbucks digital cards.',
    },
    {
      id: 'a26',
      timestamp: getDateTimeString(4, 2),
      type: 'SAVINGS',
      description: 'Awarded 260 Nova to Jamie W. for off-peak charging at 2:00 AM.',
    },
    {
      id: 'a27',
      timestamp: getDateTimeString(5, 10),
      type: 'PURCHASE',
      description: 'Purchased 2,000 Nova ($200) - Manual top-up.',
    },
    {
      id: 'a28',
      timestamp: getDateTimeString(6, 3),
      type: 'SAVINGS',
      description: 'Awarded 250 Nova to Quinn B. for off-peak charging at 3:00 AM.',
    },
  ],
  novaBudget: {
    total: 10000,
    spent: 6200,
    remaining: 3800,
    totalUsd: 1000,
    projectedRunoutDate: getDateString(-20),
  },
  autoTopUpConfig: {
    enabled: false,
    threshold: 2000,
    topUpAmountUsd: 300,
    topUpAmountNova: 3000,
    frequency: 'Max 2 per month',
  },
}

// Export all mock data
export const mockProperties = [
  property1Data.property,
  property2Data.property,
]

export const mockDashboardData: Record<string, DashboardData> = {
  'standard-domain': property1Data,
  'bridge-kenzie': property2Data,
}

