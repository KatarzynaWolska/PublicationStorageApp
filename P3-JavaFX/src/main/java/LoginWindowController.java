import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.control.Alert;
import javafx.scene.control.TextField;
import javafx.scene.layout.StackPane;
import javafx.stage.Stage;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.message.BasicHeader;
import org.apache.http.protocol.HTTP;
import org.apache.http.util.EntityUtils;
import org.json.JSONObject;
import java.net.URL;


public class LoginWindowController {

    @FXML
    private StackPane stackPaneLogin;

    @FXML
    private TextField loginTextField;

    @FXML
    private TextField passwordTextField;

    private String token;
    private String username;
    private String publicationsURL;
    private CloseableHttpClient httpClient;
    private Utils utils;

    @FXML
    public void initialize() {
        utils = new Utils();
        httpClient = utils.httpClient;
    }

    public void logIn(ActionEvent actionEvent) {
        String login = loginTextField.getText();
        String password = passwordTextField.getText();

        try {
            JSONObject credentialsJSON = new JSONObject();
            credentialsJSON.put("username", login);
            credentialsJSON.put("password", password);

            HttpPost request = new HttpPost("https://api.company.com:443/login_user");

            StringEntity se = new StringEntity(credentialsJSON.toString());
            se.setContentType(new BasicHeader(HTTP.CONTENT_TYPE, "application/json"));
            request.setEntity(se);
            HttpResponse response = httpClient.execute(request);

            if (response != null) {
                String json = EntityUtils.toString(response.getEntity());
                JSONObject responseJSON = new JSONObject(json);

                if (response.getStatusLine().getStatusCode() == 200) { // POZMIENIAC TE KODY
                    String publicationsURL = responseJSON.getJSONObject("_links").getJSONObject("publications").get("href").toString();
                    String path = new URL(publicationsURL).getPath();
                    String requestURL = utils.baseURL + path;
                    this.publicationsURL = requestURL;
                    this.token = responseJSON.get("token").toString();
                    this.username = login;

                    WelcomeWindowController controller = new WelcomeWindowController(username, token, publicationsURL);
                    FXMLLoader loader = new FXMLLoader(getClass().getResource("welcomeWindow.fxml"));
                    Stage stage = (Stage) loginTextField.getParent().getScene().getWindow();
                    loader.setController(controller);

                    utils.switchView(loader, stage);
                }
                else {
                    Alert alert = new Alert(Alert.AlertType.INFORMATION);
                    alert.setTitle("Error");
                    alert.setHeaderText(responseJSON.get("message").toString());
                    alert.showAndWait();
                }
            }

        } catch (Exception e) {
            e.printStackTrace();
        }

    }
}
