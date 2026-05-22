import { describe, expect, it } from 'vitest'
import { computePresetRange } from './periodPresets'

// 2026-05-21, built from local year/month/day so it matches what the
// function reads back with getFullYear / getMonth / getDate.
const NOW = new Date(2026, 4, 21)

describe('computePresetRange', () => {
  it('applies no filter for "all"', () => {
    expect(computePresetRange('all', NOW)).toEqual({ from: '', to: '' })
  })

  it('starts "1y" one calendar year before now', () => {
    expect(computePresetRange('1y', NOW)).toEqual({
      from: '2025-05-21',
      to: '2026-05-21',
    })
  })

  it('starts "2y" two calendar years before now', () => {
    expect(computePresetRange('2y', NOW)).toEqual({
      from: '2024-05-21',
      to: '2026-05-21',
    })
  })

  it('starts "3y" three calendar years before now', () => {
    expect(computePresetRange('3y', NOW)).toEqual({
      from: '2023-05-21',
      to: '2026-05-21',
    })
  })

  it('zero-pads single-digit months and days', () => {
    expect(computePresetRange('1y', new Date(2025, 0, 5))).toEqual({
      from: '2024-01-05',
      to: '2025-01-05',
    })
  })
})
