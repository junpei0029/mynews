//OAuthリクエスト用の関数
function hatena_oauth($request_url,$method,$parameters){
  $key = 'BJIpFUnXoRMk4Q==';    //コンシューマーキー
  $pass = '+2vCyqFiehc6MeBBzct4H1/CIss=';   //コンシューマーシークレット

  $url = 'localhost:5000/hatena_util.php';    //このプログラムのURL
  global $http_response_header;
  $oauth_parameters = array(
    'oauth_callback' => $url,
    'oauth_consumer_key' => $key,
    'oauth_nonce' => microtime(),
    'oauth_signature_method' => 'HMAC-SHA1',
    'oauth_timestamp' => time(),
    'oauth_version' => '1.0'
  );
  if(isset($parameters['oauth_token'])){$oauth_parameters['oauth_token'] = $parameters['oauth_token'];unset($parameters['oauth_token'],$oauth_parameters['oauth_callback']);}
  if(isset($parameters['oauth_token_secret'])){$oauth_token_secret = $parameters['oauth_token_secret'];unset($parameters['oauth_token_secret']);}else{$oauth_token_secret = '';}
  if(isset($parameters['oauth_verifier'])){$oauth_parameters['oauth_verifier'] = $parameters['oauth_verifier'];unset($parameters['oauth_verifier']);}
  $tail = ($method === 'GET') ? '?'.http_build_query($parameters,'','&',PHP_QUERY_RFC3986) : '';
  $all_parameters = array_merge($oauth_parameters,$parameters);
  ksort($all_parameters);
  $base_string = implode('&',array(rawurlencode($method),rawurlencode($request_url),rawurlencode(http_build_query($all_parameters,'','&',PHP_QUERY_RFC3986))));
  $key = implode('&',array(rawurlencode($pass),rawurlencode($oauth_token_secret)));
  $oauth_parameters['oauth_signature'] = base64_encode(hash_hmac('sha1', $base_string, $key, true));
  $data = array('http'=>array('method' => $method,'header' => array('Authorization: OAuth '.http_build_query($oauth_parameters,'',',',PHP_QUERY_RFC3986),),));
  if($method !== 'GET') $data['http']['content'] = http_build_query($parameters);
  $data = @file_get_contents($request_url.$tail,false,stream_context_create($data));
 
  return $data ? $data : false;
}
 
//GETクエリ形式の文字列を配列に変換する関数
function get_query($data){
  $ary = explode("&",$data);
  foreach($ary as $items){
    $item = explode("=",$items);
    $query[$item[0]] = $item[1];
  }
  return $query;
}
