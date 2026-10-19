package com.fruitfly.brain;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import javax.imageio.IIOImage;
import javax.imageio.ImageIO;
import javax.imageio.ImageTypeSpecifier;
import javax.imageio.ImageWriteParam;
import javax.imageio.ImageWriter;
import javax.imageio.metadata.IIOMetadata;
import javax.imageio.metadata.IIOMetadataNode;
import javax.imageio.stream.ImageOutputStream;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.HashMap;
import java.util.Map;

/** Demo render endpoint for an iPhone client. JDK standard library only. */
public final class Endpoint {
    static final int MAX_DPI = 1200;
    static final double MAX_IN = 20.0;
    static final long MAX_PIXELS = 40_000_000L;
    static String schemaJson;

    public static void main(String[] args) throws Exception {
        System.setProperty("java.awt.headless", "true");
        String host = System.getProperty("host", "127.0.0.1");
        int port = Integer.getInteger("port", 8025);
        Path schema = Path.of(System.getProperty("schema", "assets/render_schema.json"));
        schemaJson = Files.readString(schema, StandardCharsets.UTF_8);

        HttpServer server = HttpServer.create(new InetSocketAddress(host, port), 0);
        server.createContext("/healthz", ex -> send(ex, 200, "application/json", "{\"status\":\"ok\"}".getBytes(StandardCharsets.UTF_8)));
        server.createContext("/schema", ex -> send(ex, 200, "application/schema+json", schemaJson.getBytes(StandardCharsets.UTF_8)));
        server.createContext("/render", Endpoint::render);
        server.start();
        System.out.println("[+] Endpoint listening on http://" + host + ":" + port + " (schema " + schema.toAbsolutePath() + ")");
    }

    static void render(HttpExchange ex) throws IOException {
        if (!"GET".equals(ex.getRequestMethod())) { error(ex, 405, "method not allowed"); return; }
        Map<String, String> q = query(ex.getRequestURI().getRawQuery());
        double wIn, hIn; int dpi;
        try {
            wIn = Double.parseDouble(q.getOrDefault("widthIn", "2"));
            hIn = Double.parseDouble(q.getOrDefault("heightIn", "3"));
            dpi = Integer.parseInt(q.getOrDefault("dpi", "300"));
        } catch (NumberFormatException e) { error(ex, 400, "widthIn/heightIn must be numbers, dpi an integer"); return; }
        if (!(wIn > 0 && wIn <= MAX_IN && hIn > 0 && hIn <= MAX_IN)) { error(ex, 400, "widthIn/heightIn must be in (0, " + MAX_IN + "]"); return; }
        if (dpi < 1 || dpi > MAX_DPI) { error(ex, 400, "dpi must be in [1, " + MAX_DPI + "]"); return; }
        int w = (int) Math.round(wIn * dpi), h = (int) Math.round(hIn * dpi);
        if (w < 1 || h < 1 || (long) w * h > MAX_PIXELS) { error(ex, 400, "image too large (max " + MAX_PIXELS + " px)"); return; }

        BufferedImage img = new BufferedImage(w, h, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = img.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        g.setColor(Color.WHITE); g.fillRect(0, 0, w, h);
        g.setColor(new Color(20, 60, 140));
        g.setStroke(new BasicStroke(Math.max(1f, dpi / 100f)));
        int m = Math.max(2, dpi / 20);
        g.drawRect(m, m, w - 2 * m, h - 2 * m);
        g.setColor(Color.BLACK);
        int fs = Math.max(8, Math.min(w, h) / 14);
        g.setFont(new Font(Font.SANS_SERIF, Font.BOLD, fs));
        String[] lines = {
            dpi + " dpi",
            fmt(wIn) + " x " + fmt(hIn) + " in",
            w + " x " + h + " px",
            Instant.now().truncatedTo(ChronoUnit.SECONDS).toString()
        };
        int y = m + fs * 2;
        for (String s : lines) { g.drawString(s, m * 2, y); y += (int) (fs * 1.4); g.setFont(new Font(Font.SANS_SERIF, Font.PLAIN, fs)); }
        g.dispose();

        byte[] png = writePng(img, dpi);
        ex.getResponseHeaders().set("X-Render-Pixel-Width", String.valueOf(w));
        ex.getResponseHeaders().set("X-Render-Pixel-Height", String.valueOf(h));
        ex.getResponseHeaders().set("X-Render-Dpi", String.valueOf(dpi));
        ex.getResponseHeaders().set("X-Render-Pixels-Per-Meter", String.valueOf(Math.round(dpi / 0.0254)));
        send(ex, 200, "image/png", png);
    }

    /** Writes PNG with pHYs = round(dpi / 0.0254) pixels per metre (unit = metre). */
    static byte[] writePng(BufferedImage img, int dpi) throws IOException {
        ImageWriter writer = ImageIO.getImageWritersByFormatName("png").next();
        ImageWriteParam param = writer.getDefaultWriteParam();
        IIOMetadata meta = writer.getDefaultImageMetadata(ImageTypeSpecifier.createFromRenderedImage(img), param);
        String ppm = String.valueOf(Math.round(dpi / 0.0254));
        IIOMetadataNode phys = new IIOMetadataNode("pHYs");
        phys.setAttribute("pixelsPerUnitXAxis", ppm);
        phys.setAttribute("pixelsPerUnitYAxis", ppm);
        phys.setAttribute("unitSpecifier", "meter");
        IIOMetadataNode root = new IIOMetadataNode("javax_imageio_png_1.0");
        root.appendChild(phys);
        meta.mergeTree("javax_imageio_png_1.0", root);
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        try (ImageOutputStream ios = ImageIO.createImageOutputStream(bos)) {
            writer.setOutput(ios);
            writer.write(null, new IIOImage(img, null, meta), param);
        } finally { writer.dispose(); }
        return bos.toByteArray();
    }

    static String fmt(double d) { return d == Math.rint(d) ? String.valueOf((long) d) : String.valueOf(d); }

    static Map<String, String> query(String raw) {
        Map<String, String> m = new HashMap<>();
        if (raw == null || raw.isEmpty()) return m;
        for (String kv : raw.split("&")) {
            int i = kv.indexOf('=');
            String k = URLDecoder.decode(i < 0 ? kv : kv.substring(0, i), StandardCharsets.UTF_8);
            String v = i < 0 ? "" : URLDecoder.decode(kv.substring(i + 1), StandardCharsets.UTF_8);
            m.put(k, v);
        }
        return m;
    }

    static void error(HttpExchange ex, int code, String msg) throws IOException {
        send(ex, code, "application/json", ("{\"error\":\"" + msg.replace("\"", "'") + "\"}").getBytes(StandardCharsets.UTF_8));
    }

    static void send(HttpExchange ex, int code, String type, byte[] body) throws IOException {
        ex.getResponseHeaders().set("Content-Type", type);
        ex.sendResponseHeaders(code, body.length);
        try (OutputStream os = ex.getResponseBody()) { os.write(body); }
    }
}
