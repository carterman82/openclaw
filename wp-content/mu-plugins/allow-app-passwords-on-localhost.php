<?php
/**
 * Allow WordPress Application Passwords on the local HTTP dev site.
 *
 * Application Passwords are normally HTTPS-only. This project binds WordPress
 * to 127.0.0.1 for local development, so plain HTTP is acceptable here.
 */

add_filter('wp_is_application_passwords_available', '__return_true');
