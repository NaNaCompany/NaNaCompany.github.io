/**
 * NaNa Company Contact Form Handler using EmailJS
 */

// TODO: Replace these with your actual EmailJS keys
const EMAILJS_SERVICE_ID = 'service_nicpl0u';
const EMAILJS_TEMPLATE_ID = 'template_h4ve5sp';
const EMAILJS_PUBLIC_KEY = '61GtFyVFJ4xDftkIG';

// Initialize EmailJS
(function () {
    emailjs.init(EMAILJS_PUBLIC_KEY);
})();

document.getElementById('contact-form').addEventListener('submit', function (event) {
    event.preventDefault();

    // Change button text to indicate loading
    const btn = this.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.textContent = '전송 중... (Sending...)';
    btn.disabled = true;

    // Send the form using EmailJS
    emailjs.sendForm(EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, this)
        .then(function () {
            alert('문의가 성공적으로 전송되었습니다! (Email sent successfully!)');
            document.getElementById('contact-form').reset();
            btn.textContent = originalText;
            btn.disabled = false;
        }, function (error) {
            console.error('EmailJS Error:', error);
            alert('메일 전송에 실패했습니다: ' + JSON.stringify(error));
            btn.textContent = originalText;
            btn.disabled = false;
        });
});
