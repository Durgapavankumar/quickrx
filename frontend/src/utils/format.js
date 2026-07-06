// Prefix "Dr." only when the clinician didn't already type it.
export function formatDoctor(name) {
  if (!name) return "";
  return /^dr\.?\s/i.test(name) ? name : `Dr. ${name}`;
}
