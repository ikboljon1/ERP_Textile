
let inactivityTimeout;

function resetTimer() {
  clearTimeout(inactivityTimeout);
  inactivityTimeout = setTimeout(showWarning, 15000); // Показать предупреждение через 15 секунд
}

function showWarning() {
  // Показать уведомление пользователю о скором выходе
  // ...

  // Установить таймаут на выход через 5 секунд
  inactivityTimeout = setTimeout(logout, 20000);
}

function logout() {
  // Выполните AJAX-запрос к Django для выхода пользователя
  // или перенаправьте пользователя на страницу выхода
  window.location.href = '/logout/';
}

// Сбрасывать таймер при каждом движении мыши или нажатии клавиши
document.addEventListener('mousemove', resetTimer);
document.addEventListener('keydown', resetTimer);

// Запустить таймер при загрузке страницы
resetTimer();