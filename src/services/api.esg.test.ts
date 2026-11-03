import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, fetchEsgMetric, overrideEsgMetric } from './api';
import { jsonResponse, overriddenEsg } from '../test/esgFixtures';

afterEach(() => vi.unstubAllGlobals());

describe('overrideEsgMetric', () => {
  it('PUTs value and reason to the override endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, overriddenEsg));
    vi.stubGlobal('fetch', fetchMock);

    const result = await overrideEsgMetric('1234567890', { value: 70, reason: 'Provider restated revenue.' });

    expect(result).toEqual(overriddenEsg);
    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/portfolio/1234567890/esg/override', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value: 70, reason: 'Provider restated revenue.' }),
    });
  });

  it('maps FastAPI 422 details to field errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(422, {
      detail: [
        { loc: ['body', 'value'], msg: 'Input should be greater than or equal to 0' },
        { loc: ['body', 'reason'], msg: 'Value error, Reason must be at least 10 characters' },
      ],
    })));

    const error = await overrideEsgMetric('1234567890', { value: -1, reason: 'short' }).catch((e) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(422);
    expect(error.fieldErrors).toEqual({
      value: 'Input should be greater than or equal to 0',
      reason: 'Reason must be at least 10 characters',
    });
  });

  it('surfaces string details such as the 409 no-metric conflict', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(409, { detail: 'No ESG metric exists for this account yet' })));

    await expect(overrideEsgMetric('1234567890', { value: 1, reason: 'Provider restated revenue.' }))
      .rejects.toMatchObject({ status: 409, message: 'No ESG metric exists for this account yet' });
  });

  it('reports network failures', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));

    await expect(fetchEsgMetric('1234567890')).rejects.toThrow('Unable to connect to the server');
  });
});
