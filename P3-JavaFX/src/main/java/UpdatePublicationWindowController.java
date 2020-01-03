import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.control.Alert;
import javafx.scene.control.TextField;
import javafx.stage.Stage;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.HttpPut;
import org.apache.http.entity.StringEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.message.BasicHeader;
import org.apache.http.protocol.HTTP;
import org.apache.http.util.EntityUtils;
import org.json.JSONObject;

public class UpdatePublicationWindowController {

    @FXML
    private TextField titleTextField;

    @FXML
    private TextField authorsTextField;

    @FXML
    private TextField yearTextField;

    @FXML
    private TextField publisherTextField;

    private String token;
    private String URL_getUpdatePublication;
    private String URL_addPublication;
    private String URL_uploadFiles;
    private JSONObject publicationJSON;
    private CloseableHttpClient httpClient;
    private Utils utils;

    public UpdatePublicationWindowController(JSONObject publicationJSON, String URL_updateGetPublication, String URL_addPublication, String URL_uploadFiles, String token) {
        this.token = token;
        this.URL_getUpdatePublication = URL_updateGetPublication;
        this.URL_addPublication = URL_addPublication;
        this.URL_uploadFiles = URL_uploadFiles;
        this.publicationJSON = publicationJSON;
        utils = new Utils();
        httpClient = utils.httpClient;
    }

    @FXML
    public void initialize() {
        try {
            titleTextField.setText(publicationJSON.get("title").toString());
            authorsTextField.setText(publicationJSON.get("authors").toString());
            yearTextField.setText(publicationJSON.get("year").toString());
            publisherTextField.setText(publicationJSON.get("publisher").toString());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void sendUpdatedPublication(ActionEvent actionEvent) {
        try {
            JSONObject pubToSend = new JSONObject();
            pubToSend.put("title", titleTextField.getText());
            pubToSend.put("authors", authorsTextField.getText());
            pubToSend.put("year", yearTextField.getText());
            pubToSend.put("publisher", publisherTextField.getText());

            HttpPut request = new HttpPut(URL_getUpdatePublication);
            StringEntity se = new StringEntity(pubToSend.toString());
            se.setContentType(new BasicHeader(HTTP.CONTENT_TYPE, "application/json"));
            request.setEntity(se);
            request.setHeader(new BasicHeader("Authorization", token));
            HttpResponse response = httpClient.execute(request);

            String json = EntityUtils.toString(response.getEntity());
            JSONObject responseJSON = new JSONObject(json);

            if (response.getStatusLine().getStatusCode() == 200) {
                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle(responseJSON.get("message").toString());
                alert.setHeaderText(responseJSON.get("message").toString());
                alert.showAndWait();

                PublicationWindowController controller = new PublicationWindowController(URL_getUpdatePublication, URL_uploadFiles, URL_addPublication, token);
                FXMLLoader loader = new FXMLLoader(getClass().getResource("publicationWindow.fxml"));
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
