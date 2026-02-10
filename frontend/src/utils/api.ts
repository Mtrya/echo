let _baseUrl = ''

export function setApiBaseUrl(url: string): void {
  _baseUrl = url
}

export function apiUrl(path: string): string {
  return _baseUrl + path
}
