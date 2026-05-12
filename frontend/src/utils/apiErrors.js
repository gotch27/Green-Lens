const ERROR_TRANSLATIONS = {
  'Invalid username or password.': 'Невалидно корисничко име или лозинка.',
  'Invalid credentials. Please try again.': 'Невалидни податоци за најава. Обидете се повторно.',
  'Username already exists.': 'Корисничкото име веќе постои.',
  'Email already exists.': 'Е-поштата веќе постои.',
  'Unable to create user.': 'Не може да се креира корисник.',
  'Invalid image format.': 'Невалиден формат на слика.',
  'Image size too large.': 'Сликата е преголема.',
  'ML service unavailable.': 'Сервисот за анализа моментално не е достапен.',
  'Scan not found.': 'Скенирањето не е пронајдено.',
  'Scan image not found.': 'Сликата од скенирањето не е пронајдена.',
  'Missing city.': 'Недостасува град.',
  'This password is too common.': 'Оваа лозинка е премногу честа.',
  'This password is entirely numeric.': 'Лозинката не смее да биде составена само од броеви.',
  'This password is too short. It must contain at least 8 characters.': 'Лозинката е прекратка. Мора да има најмалку 8 знаци.',
  'The password is too similar to the username.': 'Лозинката е премногу слична на корисничкото име.',
  'The password is too similar to the email.': 'Лозинката е премногу слична на е-поштата.',
  'Ensure this field has at least 8 characters.': 'Полето мора да има најмалку 8 знаци.',
  'Enter a valid email address.': 'Внесете валидна е-пошта.',
  'This field may not be blank.': 'Ова поле не смее да биде празно.',
};

function firstMessage(value) {
  if (Array.isArray(value)) return value[0];
  return value;
}

export function translateApiMessage(message) {
  if (!message) return message;
  return ERROR_TRANSLATIONS[message] || message;
}

export function getApiErrorMessage(error, fallback, fields = []) {
  const data = error.response?.data;
  const candidates = [
    data?.error,
    data?.detail,
    data?.non_field_errors?.[0],
    ...fields.map(field => firstMessage(data?.[field])),
    fallback,
  ];
  return translateApiMessage(candidates.find(Boolean));
}
