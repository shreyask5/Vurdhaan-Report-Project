/**
 * Email Validation Utilities
 * Validates business emails by blocking consumer email domains
 */

// List of consumer email domains that should be blocked for business signups
const CONSUMER_EMAIL_DOMAINS = [
  'gmail.com',
  'outlook.com',
  'yahoo.com',
  'hotmail.com',
  'aol.com',
  'icloud.com',
  'protonmail.com',
  'proton.me',
  'mail.com',
  'zoho.com',
  'gmx.com',
  'gmx.net',
  'yandex.com',
  'yandex.ru',
  'live.com',
  'msn.com',
  'me.com',
  'mac.com',
  'inbox.com',
  'mailinator.com',
  'guerrillamail.com',
  'temp-mail.org',
  'tempmail.com',
  'throwaway.email',
  'cock.li',
  'rediffmail.com',
  'qq.com',
  '163.com',
  '126.com',
];

/**
 * Check if an email is a business email (not from consumer domains)
 * @param email - Email address to validate
 * @returns true if business email, false if consumer email
 */
export function isBusinessEmail(email: string): boolean {
  if (!email || typeof email !== 'string') {
    return false;
  }

  // Extract domain from email
  const emailParts = email.toLowerCase().trim().split('@');

  if (emailParts.length !== 2) {
    return false;
  }

  const domain = emailParts[1];

  // Check if domain is in consumer list
  return !CONSUMER_EMAIL_DOMAINS.includes(domain);
}

/**
 * Get a user-friendly error message for consumer email domains
 * @param email - Email address
 * @returns Error message string
 */
export function getBusinessEmailError(email: string): string {
  const emailParts = email.toLowerCase().trim().split('@');
  const domain = emailParts.length === 2 ? emailParts[1] : '';

  if (CONSUMER_EMAIL_DOMAINS.includes(domain)) {
    return `Please use your work or business email address. Consumer email addresses from ${domain} are not allowed.`;
  }

  return 'Please use a valid business email address.';
}

/**
 * Export consumer domains list for reference
 */
export { CONSUMER_EMAIL_DOMAINS };
