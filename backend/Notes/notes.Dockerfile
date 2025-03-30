# notes.dockerfile
FROM php:8.2-cli

# Install required PHP extensions
RUN docker-php-ext-install pdo pdo_mysql

# Set working directory
WORKDIR /var/www/html

# Copy files into container
COPY . .

# Expose the app on port 8003
EXPOSE 8003

# Start PHP dev server on port 8003
CMD ["php", "-S", "0.0.0.0:8003"]
