<?php
$request_uri = $_SERVER['REQUEST_URI'];

// Database config
$host = 'host.docker.internal';
$db = 'notes_db';
$user = 'root';
$pass = '';

// Handle: /notes.php/list — return JSON of all notes_id
if (preg_match('/\/notes\.php\/list/', $request_uri)) {
    header('Content-Type: application/json');

    try {
        $pdo = new PDO("mysql:host=$host;dbname=$db", $user, $pass);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        $stmt = $pdo->query("SELECT notes_id FROM notes ORDER BY notes_id ASC");
        $notes = $stmt->fetchAll(PDO::FETCH_ASSOC);

        echo json_encode($notes);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(["error" => $e->getMessage()]);
    }
    exit;
}

// Handle: /notes.php/notes_<id> — download the corresponding PDF
if (preg_match('/\/notes\.php\/notes_(\d+)/', $request_uri, $matches)) {
    $notes_id = intval($matches[1]);
} else {
    http_response_code(400);
    echo "Invalid URL format. Use /notes.php/<notesId> or /notes.php/list";
    exit;
}

try {
    $pdo = new PDO("mysql:host=$host;dbname=$db", $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $stmt = $pdo->prepare("SELECT fileName FROM notes WHERE notesId = ?");
    $stmt->execute([$notesId]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($row) {
        $filename = basename($row['fileName']);
        $filepath = __DIR__ . "/notes/" . $filename;

        if (file_exists($filepath)) {
            header('Content-Description: File Transfer');
            header('Content-Type: application/pdf');
            header('Content-Disposition: attachment; filename="' . $filename . '"');
            header('Expires: 0');
            header('Cache-Control: must-revalidate');
            header('Pragma: public');
            header('Content-Length: ' . filesize($filepath));
            ob_clean();
            flush();
            readfile($filepath);
            exit;
        } else {
            http_response_code(404);
            echo "File not found.";
        }
    } else {
        http_response_code(404);
        echo "No file found for notesId $notesId.";
    }
} catch (PDOException $e) {
    http_response_code(500);
    echo "Database error: " . $e->getMessage();
}
