<?php

class EmbeddingAPI {
    private $db;
    private $pythonScriptPath;

    public function __construct($dbPath, $pythonScriptPath = null, $graphPath = null) {
        $this->db = new Database($dbPath);
        $this->pythonScriptPath = $pythonScriptPath ?: __DIR__ . '../lightWikiBackEnd/lib3d.py';
        $this->graphPath = graphPath ?: __DIR__ . '../lightWikiBackEnd/graph.json';
    }

    public function get_blobs(){
        $sql = "SELECT p.embedding 
                FROM pages p";

        $embeddings = $this->db->fetchAll($sql);

        return {
            "blobs" => $embeddings
        }
    }

    private function get_page_info($blob){
        $sql = "SELECT p.id, p.title, p.created_at
                FROM pages p
                WHERE embedding = $blob"
        
        $info = $this->db->fetchAll($sql);

        return $info
    }

    public function create_graph(){
        $blobs = $this->get_embeddings()

        $graph = shell_exec("lightwiki_env/bin/python " + $pythonScriptPath + "graph_nearest $blobs")

        if (file_put_contents($this->graphPath, $graph)) {
            echo "File JSON salvato con successo!";
        } else {
            echo "Errore nel salvataggio del file.";
        }
    }

    public function get_graph(){
        $graph = file_get_contents($graphPath);
        return $graph
    }

    public function search($text){
        $blob = shell_exec("lightwiki_env/bin/python  $pythonScriptPath get_blob $text")
        $blobs = get_blobs()
        $nearest_blobs = shell_exec("lightwiki_env/bin/python  $pythonScriptPath k_nearest $blob 5 $blobs")
        $info = [];
        foreach($nearest_blobs["blobs"] as $blob_a){
            $info[] = get_page_info($blob_a)
        }
         
        return $info
    }

}

?>