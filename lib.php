<?php
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

require_once __DIR__ . "../core/db.php";

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
            "blobs" => $blobs
        ];

        return json_encode($result);
        
    }

    private function get_page_info($blob){
        $sql = "SELECT p.id, p.title, p.created_at
                FROM pages p
                WHERE embedding = ?";
        
        $info = $this->db->fetchAll($sql, [$blob]);
        return $info;
    }

    public function create_graph(){
        $blobs = $this->get_blobs();

        $graph = shell_exec("lightwiki_env/bin/python " . $this->pythonScriptPath . " graph_nearest " . json_encode($blobs));

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
        $blob = shell_exec("lightwiki_env/bin/python " . $this->pythonScriptPath . " get_blob " . $text);
        $blobs = $this->get_blobs();
        $nearest_blobs = shell_exec("lightwiki_env/bin/python " . $this->pythonScriptPath . " k_nearest " . $blob . " 5 " . json_encode($blobs));
        $nearest_blobs_data = json_decode($nearest_blobs, true);
        
        $info = array();
        foreach($nearest_blobs_data["blobs"] as $blob_a){
            $info[] = $this->get_page_info($blob_a);
        }
         
        return $info;
    }

}

// USO DELL'API
header('Content-Type: application/json');

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