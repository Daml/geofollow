package main

import (
	"encoding/json"
	"fmt"
	"golang.org/x/net/websocket"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"strings"
)

// Pool management
// ===============

type Pool map[string][]chan []byte

func (p Pool) Register(name string, ch chan []byte) {
	p[name] = append(p[name], ch)
}

func (p Pool) Broadcast(name string, payload map[string]string) {
	bytes, err := json.Marshal(payload)
	if err != nil {
		log.Printf("JSON ERROR : %+v", err)
		return
	}

	for _, listener := range p[name] {
		select {
		case listener <- bytes:
		default:
		}
	}
}

func (p Pool) Free(name string, ch chan []byte) {
	for idx, listener := range p[name] {
		if listener == ch {
			p[name][len(p[name])-1], p[name][idx] = p[name][idx], p[name][len(p[name])-1]
			p[name] = p[name][:len(p[name])-1]
			return
		}
	}
}

// RAW TCP Handler
// ===============

func NetHandler(c net.Conn) {
	var buf = make([]byte, 1024)
	log.Printf("%s TCP Connection ...\n", c.RemoteAddr().String())

	n, err := c.Read(buf)
	if err != nil {
		log.Fatalln("read messed up", err.Error())
		panic(err)
	}

	track := strings.TrimSuffix(string(buf[0:n]), "\n")

	log.Printf("%s TCP Register %s\n", c.RemoteAddr().String(), track)

	queue := make(chan []byte)

	defer func() {
		log.Printf("%s TCP Freeing", c.RemoteAddr().String())
		pool.Free(track, queue)
		close(queue)
		c.Close()
	}()

	pool.Register(track, queue)

	for msg := range queue {
		_, err := c.Write(msg)
		if err != nil {
			return
		}
		c.Write([]byte("\n"))
	}
}

func TCPServer() {
	log.Printf("Listen on tcp4 :9999")

	l, err := net.Listen("tcp4", ":9999")
	if err != nil {
		log.Fatal(err)
	}

	defer l.Close()

	for {
		c, err := l.Accept()
		if err != nil {
			fmt.Println(err)
			return
		}
		go NetHandler(c)
	}
}

// Websocket handler
// =================

func WebSockHandler(ws *websocket.Conn) {
	r := ws.Request()

	if err := r.ParseForm(); err != nil {
		log.Printf("Error parsing form: %s", err)
		return
	}

	track := r.Form.Get("track")

	queue := make(chan []byte)

	pool.Register(track, queue)

	for msg := range queue {
		ws.Write(msg)
	}
}

// WMS HTTP Handler
// ================

func WMSHandler(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		log.Printf("Error parsing form: %s", err)
		return
	}

	track := r.Form.Get("track")
	request := r.Form.Get("REQUEST")

	switch request {
	case "GetCapabilities":
		log.Printf("%s WMS GetCapabilites(%s)", r.RemoteAddr, track)
		cap, err := os.OpenFile("capabilities.xml", os.O_RDONLY, 0)
		if err != nil {
			http.Error(w, "Loutrage", 500)
			return
		}
		w.Header().Add("Content-Type", "application/xml")
		io.Copy(w, cap)
		cap.Close()

	case "GetMap":
		bbox := r.Form.Get("BBOX")
		width := r.Form.Get("WIDTH")
		height := r.Form.Get("HEIGHT")
		log.Printf("%s WMS GetMap(%s) = %sx%s (%s)", r.RemoteAddr, track, width, height, bbox)
		m := map[string]string{"w": width, "h": height, "b": bbox}
		pool.Broadcast(track, m)
	default:
		log.Printf("%s WMS Not Implemented : %s", r.RemoteAddr, request)
		http.Error(w, "Not Implemented", 501)
	}
}

// Main routine
// ============

var pool = Pool{}

func main() {
	go TCPServer()

	http.Handle("/follow", websocket.Handler(WebSockHandler))
	http.HandleFunc("/wms", WMSHandler)
	http.HandleFunc("/debug", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("DEBUG : %+v", pool)
		http.Error(w, "Not found", 404)
	})
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		http.Error(w, "Not found", 404)
	})

	log.Fatal(http.ListenAndServe(":8000", nil))
}
