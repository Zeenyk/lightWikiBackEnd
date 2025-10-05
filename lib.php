<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

require_once __DIR__ . "../core/db.php";
require_once __DIR__ . "../core/config.php";

$config = include __DIR__ . "../core/config.php";

class EmbeddingAPI {
    private $db;
    private $pythonScriptPath;
    private $graphPath;
    
    public function __construct($dbPath, $pythonScriptPath = null, $graphPath = null) {
        $this->db = new Database($dbPath);
        $this->pythonScriptPath = $pythonScriptPath ?: __DIR__ . '/../lightWikiBackEnd/lib3d.py';
        $this->graphPath = $graphPath ?: __DIR__ . '/../lightWikiBackEnd/graph.json';
    }

    public function get_blobs(){
        $sql = "SELECT p.embedding
                FROM pages p";

        $blobs = $this->db->fetchAll($sql);

        $result = [
            "blobs" => array_map('base64_encode', $blobs)
        ];

        return json_encode($result);

    }

    private function get_page_info($blob_b64){
        $blob = base64_decode($blob_b64);
        $sql = "SELECT p.id, p.title, p.created_at
                FROM pages p
                WHERE embedding = ?";

        $info = $this->db->fetchAll($sql, [$blob]);
        return $info;
    }

    public function create_graph(){
        $blobs = $this->get_blobs();

        $graph = shell_exec("lightwiki_env/bin/python " . $this->pythonScriptPath . " graph_nearest " . escapeshellarg($blobs));

        if (file_put_contents($this->graphPath, $graph)) {
            return "File JSON salvato con successo!";
        } else {
            return "Errore nel salvataggio del file.";
        }
    }

    public function get_graph(){
        $graph = file_get_contents($this->graphPath);
        return $graph;
    }

    public function search($text){
        $text_esc = escapeshellarg($text);
        $blob = shell_exec("lightwiki_env/bin/python " . $this->pythonScriptPath . " get_blob " . $text_esc);
        $blobs_json = $this->get_blobs();
        $blobs_json_esc = escapeshellarg($blobs_json);
        $blob_esc = escapeshellarg(trim($blob));
        $nearest_blobs = shell_exec("lightwiki_env/bin/python " . $this->pythonScriptPath . " k_nearest " . $blob_esc . " 5 " . $blobs_json_esc);
        $nearest_blobs_data = json_decode($nearest_blobs, true);

        $info = array();
        foreach($nearest_blobs_data["embeddings"] as $item){
            $blob_a = $item["blobs"];
            $info[] = $this->get_page_info($blob_a);
        }

        return $info;
    }

}

// USO DELL'API


$api = new EmbeddingAPI("../storage/litewiki.db");

$action = $_GET['action'] ?? '';

switch($action) {
    case 'get-graph':
        echo $api->get_graph();
        break;
        
    case 'create-graph':
        echo $api->create_graph();
        break;
        
    case 'ai-search':
        $text = $_GET['q'] ?? '';
        if($text) {
            $results = $api->search($text);
            echo json_encode($results);
        } else {
            echo json_encode(array('error' => 'Parametro q mancante'));
        }
        break;
        
    case 'get-blobs':
        $blobs = $api->get_blobs();
        echo json_encode($blobs);
        break;
        
    default:
        echo json_encode(array('error' => 'Azione non valida'));
}

?>
