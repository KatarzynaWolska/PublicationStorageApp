import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.control.Alert;
import javafx.scene.control.TextField;
import javafx.stage.Stage;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.message.BasicHeader;
import org.apache.http.protocol.HTTP;
import org.apache.http.util.EntityUtils;
import org.json.JSONObject;


public class AddPublicationController {

    @FXML
    private TextField titleTextField;

    @FXML
    private TextField authorsTextField;

    @FXML
    private TextField yearTextField;

    @FXML
    private TextField publisherTextField;

    private String token;
    private CloseableHttpClient httpClient;
    private Utils utils;
    private String URL_addPublication;

    public AddPublicationController(String token, String URL_publication) {
        this.token = token;
        utils = new Utils();
        httpClient = utils.httpClient;
        this.URL_addPublication = URL_publication;
    }

    public void sendPublication(ActionEvent actionEvent) {
        try {
            JSONObject pubToSend = new JSONObject();
            pubToSend.put("title", titleTextField.getText());
            pubToSend.put("authors", authorsTextField.getText());
            pubToSend.put("year", yearTextField.getText());
            pubToSend.put("publisher", publisherTextField.getText());

            HttpPost request = new HttpPost(URL_addPublication);
            StringEntity se = new StringEntity(pubToSend.toString());
            se.setContentType(new BasicHeader(HTTP.CONTENT_TYPE, "application/json"));
            request.setEntity(se);
            request.setHeader(new BasicHeader("Authorization", token));
            HttpResponse response = httpClient.execute(request);

            String json = EntityUtils.toString(response.getEntity());
            JSONObject responseJSON = new JSONObject(json);

            if (response.getStatusLine().getStatusCode() == 201) {
                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle("Publication added");
                alert.setHeaderText("Publication added");
                alert.showAndWait();

                PublicationsWindowController controller = new PublicationsWindowController(URL_addPublication, token);
                FXMLLoader loader = new FXMLLoader(getClass().getResource("publicationsWindow.fxml"));
                Stage stage = (Stage) titleTextField.getParent().getScene().getWindow();
                loader.setController(controller);
                utils.switchView(loader, stage);

            } else {
                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle("Error");
                alert.setHeaderText(responseJSON.get("message").toString());
                alert.showAndWait();

                if (response.getStatusLine().getStatusCode() == 401) {
                    switchViewToLogin();
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void switchViewToLogin() {
        try {
            FXMLLoader loader = new FXMLLoader(getClass().getResource("loginWindow.fxml"));
            Stage stage = (Stage) titleTextField.getParent().getScene().getWindow();
            utils.switchView(loader, stage);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
