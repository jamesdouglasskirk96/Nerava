'use client'

import { useState } from 'react'
import { Card } from '../ui/Card'
import { Badge } from '../ui/Badge'
import type { Session } from '@/lib/types/dashboard'

interface SessionsTableProps {
  sessions: Session[]
  isLoading?: boolean
}

type SortField = 'driverName' | 'dateTime' | 'sessionType' | 'energyKwh' | 'estimatedCost' | 'novaAwarded'
type SortDirection = 'asc' | 'desc'

export function SessionsTable({ sessions, isLoading = false }: SessionsTableProps) {
  const [sortField, setSortField] = useState<SortField | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const sortedSessions = [...sessions].sort((a, b) => {
    if (!sortField) return 0

    let aValue: string | number
    let bValue: string | number

    switch (sortField) {
      case 'driverName':
        aValue = a.driverName
        bValue = b.driverName
        break
      case 'dateTime':
        aValue = new Date(a.dateTime).getTime()
        bValue = new Date(b.dateTime).getTime()
        break
      case 'sessionType':
        aValue = a.sessionType
        bValue = b.sessionType
        break
      case 'energyKwh':
        aValue = a.energyKwh
        bValue = b.energyKwh
        break
      case 'estimatedCost':
        aValue = a.estimatedCost
        bValue = b.estimatedCost
        break
      case 'novaAwarded':
        aValue = a.novaAwarded
        bValue = b.novaAwarded
        break
      default:
        return 0
    }

    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortDirection === 'asc'
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue)
    }

    return sortDirection === 'asc' ? (aValue as number) - (bValue as number) : (bValue as number) - (aValue as number)
  })

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return (
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      )
    }
    return sortDirection === 'asc' ? (
      <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
      </svg>
    ) : (
      <svg className="w-4 h-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    )
  }

  if (isLoading) {
    return (
      <Card className="animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-gray-200 rounded"></div>
          ))}
        </div>
      </Card>
    )
  }

  return (
    <Card>
      <h3 className="text-xl font-semibold text-gray-900 mb-4">Recent Sessions</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 font-semibold text-gray-700">
                <button
                  onClick={() => handleSort('driverName')}
                  className="flex items-center gap-1 hover:text-primary transition-colors"
                >
                  Driver
                  <SortIcon field="driverName" />
                </button>
              </th>
              <th className="text-left py-3 px-4 font-semibold text-gray-700">
                <button
                  onClick={() => handleSort('dateTime')}
                  className="flex items-center gap-1 hover:text-primary transition-colors"
                >
                  Date & Time
                  <SortIcon field="dateTime" />
                </button>
              </th>
              <th className="text-left py-3 px-4 font-semibold text-gray-700">
                <button
                  onClick={() => handleSort('sessionType')}
                  className="flex items-center gap-1 hover:text-primary transition-colors"
                >
                  Type
                  <SortIcon field="sessionType" />
                </button>
              </th>
              <th className="text-right py-3 px-4 font-semibold text-gray-700">
                <button
                  onClick={() => handleSort('energyKwh')}
                  className="flex items-center gap-1 hover:text-primary transition-colors ml-auto"
                >
                  Energy (kWh)
                  <SortIcon field="energyKwh" />
                </button>
              </th>
              <th className="text-right py-3 px-4 font-semibold text-gray-700">
                <button
                  onClick={() => handleSort('estimatedCost')}
                  className="flex items-center gap-1 hover:text-primary transition-colors ml-auto"
                >
                  Est. Cost
                  <SortIcon field="estimatedCost" />
                </button>
              </th>
              <th className="text-right py-3 px-4 font-semibold text-gray-700">
                <button
                  onClick={() => handleSort('novaAwarded')}
                  className="flex items-center gap-1 hover:text-primary transition-colors ml-auto"
                >
                  Nova Awarded
                  <SortIcon field="novaAwarded" />
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedSessions.map((session) => (
              <tr key={session.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <td className="py-3 px-4 font-medium text-gray-900">{session.driverName}</td>
                <td className="py-3 px-4 text-gray-600">
                  {new Date(session.dateTime).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                  })}
                </td>
                <td className="py-3 px-4">
                  <Badge variant={session.sessionType === 'off-peak' ? 'success' : 'warning'}>
                    {session.sessionType === 'off-peak' ? 'Off-peak' : 'Peak'}
                  </Badge>
                </td>
                <td className="py-3 px-4 text-right text-gray-900">{session.energyKwh.toFixed(1)}</td>
                <td className="py-3 px-4 text-right text-gray-900">${session.estimatedCost.toFixed(2)}</td>
                <td className="py-3 px-4 text-right text-gray-900">
                  {session.novaAwarded > 0 ? session.novaAwarded.toLocaleString() : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  )
}

