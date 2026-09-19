import { makeMockEvents } from "./mockData.js";

export const IS_MOCK = true;

export async function loadEvents() {
  return makeMockEvents();
}
