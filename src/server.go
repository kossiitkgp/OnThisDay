package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
)

const PORT = ":4000"
const DIR = "SavedCreds"

func main() {
	log.Println("Launching the OAuth Sever on port " + PORT[1:])
	OAuthServer()
	log.Fatal("Server shutdown!")
}

func OAuthServer() {
	// using mux instead of direct http handling
	mux := http.DefaultServeMux
	mux.HandleFunc("/init", InitHandler) // A simple button (for testing)
	log.Println("Init handler setup.")
	mux.HandleFunc("/redirect", RedirectHandler) // Redirected to code here, IMP
	log.Println("Redirect handler setup,")
	log.Println("Listening on the port...")
	err := http.ListenAndServe(PORT, mux)
	if err != nil {
		log.Println("Failed to start the server!")
		log.Fatal("%+v", err)
	}
}

func InitHandler(w http.ResponseWriter, r *http.Request) {
	// serves the test webpage to init the process
	log.Println("InitHandler accessed!")
	http.ServeFile(w, r, "src/test.html")
}

func RedirectHandler(w http.ResponseWriter, r *http.Request) {
	// Handles redirect from the slack server

	log.Println("RedirectHandler accessed!")
	AuthCode := r.URL.Query().Get("code")
	uri := "https://slack.com/api/oauth.access?code=" + r.URL.Query().Get("code") +
		"&client_id=" + os.Getenv("CLIENT_ID") +
		"&client_secret=" + os.Getenv("CLIENT_SECRET") +
		"&redirect_uri=" + os.Getenv("REDIRECT_URI")

	log.Println("Following URI generated:\n" + uri)

	GetResp, GetErr := http.Get(uri)
	if GetErr != nil {
		log.Println("Failed to authenticate with Slack")
		log.Fatal("%+v", GetErr)
	}
	log.Println("Code received successfully!")

	var JSONResp interface{}
	jsonDecoder := json.NewDecoder(GetResp.Body)
	JSONerr := jsonDecoder.Decode(&JSONResp)
	if JSONerr != nil {
		log.Fatal("Failed to decode the body")
	}
	log.Println("authenticated tokens received!")
	// fmt.Printf("%+v", JSONResp)
	SaveCred(JSONResp, AuthCode+".temp")
}

func SaveCred(JSONResp interface{}, FileName string) {
	CheckDir()
	path := fmt.Sprint(DIR, FileName)
	os.Remove(path)
	log.Println("Creds being saved to " + path)

	ToSave, MarshalErr := json.Marshal(JSONResp)
	if MarshalErr != nil {
		log.Println("Failed to save creds")
		log.Printf("%+v", MarshalErr)
	}
	ioutil.WriteFile(path, ToSave, 0644)
}

func CheckDir() {
	_, DirErr := os.Stat(DIR)
	if DirErr != nil {
		if os.IsNotExist(DirErr) {
			os.Mkdir(DIR, 0755)
		} else {
			log.Println(DirErr)
		}
	}
}
