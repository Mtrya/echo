let _baseUrl = ''

export function setApiBaseUrl(url) {
  _baseUrl = url
}

export function apiUrl(path) {
  return _baseUrl + path
}
