<?php
header("Access-Control-Allow-Origin: *");
$request_uri = $_SERVER['REQUEST_URI'];

// Database config
$host = 'mysql';
$db = 'course';
$user = 'is213';
$pass = 'password';

// Handle: /notes.php/<courseId>/<notesId> — download PDF
if (preg_match('/\/notes\.php\/([^\/]+)\/([^\/]+)/', $request_uri, $matches)) {
    $courseId = $matches[1];
    $notesId = $matches[2];
} else {
    http_response_code(400);
    echo "Invalid URL format. Use /notes.php/<courseId>/<notesId> or /notes.php/list";
    exit;
}

try {
    $pdo = new PDO("mysql:host=$host;dbname=$db", $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $stmt = $pdo->prepare("SELECT fileName FROM notes WHERE courseId = ? AND notesId = ?");
    $stmt->execute([$courseId, $notesId]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($row) {
        $filename = basename($row['fileName']);
        $filepath = __DIR__ . "/notes_compiled/" . $filename;

        if (file_exists($filepath)) {
            header('Content-Description: File Transfer');
            header('Content-Type: application/pdf');
            header('Content-Disposition: inline; filename="' . $filename . '"');
            header('Expires: 0');
            header('Cache-Control: must-revalidate');
            header('Pragma: public');
            header('Content-Length: ' . filesize($filepath));
            if (ob_get_length()) ob_end_clean();
            flush();
            readfile($filepath);
            exit;
        } else {
            http_response_code(404);
            echo "File not found.";
        }
    } else {
        http_response_code(404);
        echo "No file found for courseId $courseId and notesId $notesId.";
    }
} catch (PDOException $e) {
    http_response_code(500);
    echo "Database error: " . $e->getMessage();
}
