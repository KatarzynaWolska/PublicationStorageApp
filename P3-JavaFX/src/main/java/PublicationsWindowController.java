import javafx.application.Platform;
import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.control.Alert;
import javafx.scene.control.Button;
import javafx.scene.layout.VBox;
import javafx.stage.Stage;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.message.BasicHeader;
import org.apache.http.util.EntityUtils;
import org.json.JSONArray;
import org.json.JSONObject;

import java.net.URL;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

public class PublicationsWindowController {

    @FXML
    private VBox VBoxPublications;

    @FXML
    private VBox publicationsListVBox;

    private JSONObject publicationsJSON;
    private CloseableHttpClient httpClient;
    private Utils utils;
    private String token;
    private String getAddPublicationsURL;

    private Map linksGetUpdateDeletePub;
    private Map linksUploadGetFiles;
    private Map pubTitleToID;

    @FXML
    public void initialize() {
        try {
            getPublications();
            if (publicationsJSON != null) {
                String pubs = publicationsJSON.get("pubs").toString();
                JSONArray pubsArray = new JSONArray(pubs);

                String links = publicationsJSON.get("_links").toString();
                JSONObject linksJSON = new JSONObject(links);

                publicationsListVBox.setSpacing(10);

                if (pubsArray.length() > 0) {
                    for (int i = 0; i < pubsArray.length(); i++) {
                        JSONObject pub = pubsArray.getJSONObject(i);
                        this.pubTitleToID.put(pub.get("title").toString(), pub.get("pub_id").toString());

                        Button pubButton = new Button(pub.get("title").toString());
                        pubButton.setOnAction(this::clickOnPublication);
                        publicationsListVBox.getChildren().add(pubButton);
                    }
                }

                Iterator<String> keys = linksJSON.keys();

                while (keys.hasNext()) {
                    String key = keys.next();

                    if (!key.equals("self")) {
                        JSONArray linkArray = linksJSON.getJSONArray(key);

                        for (int i = 0; i < linkArray.length(); i++) {
                            JSONObject linkJSON = linkArray.getJSONObject(i);

                            String path = new URL(linkJSON.get("href").toString()).getPath();
                            String requestURL = utils.baseURL + path;

                            if (linkJSON.get("name").toString().equals("get_update_or_delete_pub")) {
                                this.linksGetUpdateDeletePub.put(key, requestURL);
                            } else if (linkJSON.get("name").toString().equals("upload_or_get_files")) {
                                this.linksUploadGetFiles.put(key, requestURL);
                            }
                        }
                    }
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public PublicationsWindowController(String getAddPublicationsURL, String token) {
        this.token = token;
        this.linksGetUpdateDeletePub = new HashMap<String, String>();
        this.linksUploadGetFiles = new HashMap<String, String>();
        this.pubTitleToID = new HashMap<String, String>();
        this.getAddPublicationsURL = getAddPublicationsURL;
        utils = new Utils();
        httpClient = utils.httpClient;
    }

    public void clickAddPublication(ActionEvent actionEvent) {
        try {
            AddPublicationController controller = new AddPublicationController(token, getAddPublicationsURL);
            FXMLLoader loader = new FXMLLoader(getClass().getResource("addPublicationWindow.fxml"));
            Stage stage = (Stage) VBoxPublications.getParent().getScene().getWindow();
            loader.setController(controller);
            utils.switchView(loader, stage);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void clickOnPublication(ActionEvent actionEvent) {
        String pubTitle = ((Button)actionEvent.getSource()).getText();
        String pubID = pubTitleToID.get(pubTitle).toString();

        String URL_getUpdateDeletePub = linksGetUpdateDeletePub.get(pubID).toString();
        String URL_uploadGetFiles = linksUploadGetFiles.get(pubID).toString();

        PublicationWindowController controller = new PublicationWindowController(URL_getUpdateDeletePub, URL_uploadGetFiles, getAddPublicationsURL, token);
        FXMLLoader loader = new FXMLLoader(getClass().getResource("publicationWindow.fxml"));
        Stage stage = (Stage) VBoxPublications.getParent().getScene().getWindow();
        loader.setController(controller);
        utils.switchView(loader, stage);
    }

    public void logOut(ActionEvent actionEvent) {
        switchViewToLogin();
    }

    private void switchViewToLogin() {
        try {
            FXMLLoader loader = new FXMLLoader(getClass().getResource("loginWindow.fxml"));
            Stage stage = (Stage) publicationsListVBox.getParent().getScene().getWindow();
            utils.switchView(loader, stage);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void getPublications() {
        try {
            HttpGet request = new HttpGet(getAddPublicationsURL);
            request.setHeader(new BasicHeader("Authorization", token));
            HttpResponse response = httpClient.execute(request);

            String json = EntityUtils.toString(response.getEntity());
            JSONObject responseJSON = new JSONObject(json);

            if (response.getStatusLine().getStatusCode() == 200) {
                this.publicationsJSON = responseJSON;
            } else {
                Alert alert = new Alert(Alert.AlertType.INFORMATION);
                alert.setTitle("Error");
                alert.setHeaderText(responseJSON.get("message").toString());
                alert.showAndWait();

                if (response.getStatusLine().getStatusCode() == 401) {
                    Platform.runLater(() -> switchViewToLogin());
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

}
