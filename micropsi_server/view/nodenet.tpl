<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>MicroPsi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="MicroPsi Nodenet editor">
    <meta name="author" content="Joscha Bach">

    <link href="static/css/bootstrap.min.css" rel="stylesheet">
    <style type="text/css">
        body {
            padding-top: 60px;
            padding-bottom: 40px;
        }

        .sidebar-nav {
            padding: 9px 0;
        }
    </style>
    <link href="static/css/bootstrap-responsive.css" rel="stylesheet">
    <link href="static/css/micropsi-styles.css" rel="stylesheet">

    <!-- HTML5 shim, for IE6-8 -->
    <!--[if lt IE 9]>
    <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
    <![endif]-->

    <link rel="shortcut icon" href="static/favicon.png">
</head>

<body>

<div class="navbar navbar-fixed-top">
    <div class="navbar-inner">
        <div class="container-fluid">
            <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </a>
            <a class="brand" href="#">MicroPsi 2 v0.1</a>

            <div class="btn-group pull-right">
                <a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
                    <i class="icon-user"></i> Administrator
                    <span class="caret"></span>
                </a>
                <ul class="dropdown-menu">
                    <li><a href="#">Change Password</a></li>
                    <li class="divider"></li>
                    <li><a href="#">Sign Out</a></li>
                </ul>
            </div>
            <div class="nav-collapse">
                <ul class="nav">
                    <li class="dropdown" id="menu_agent">
                        <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_agent">Agent
                            <b class="caret"></b></a>
                        <ul class="dropdown-menu">
                            <li><a href="#">New...</a></li>
                            <li><a href="#">Edit...</a></li>
                            <li class="divider"></li>
                            <li><a href="#">Delete</a></li>
                            <li><a href="#">Save</a></li>
                            <li><a href="#">Revert</a></li>
                            <li class="divider"></li>
                            <li><a href="#">Export to file...</a></li>
                            <li><a href="#">Import from file...</a></li>
                            <li><a href="#">Merge with file...</a></li>
                        </ul>
                    </li>
                    <li class="dropdown" id="menu_world">
                        <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_world">World
                            <b class="caret"></b></a>
                        <ul class="dropdown-menu">
                            <li><a href="#">New...</a></li>
                            <li><a href="#">Edit...</a></li>
                            <li class="divider"></li>
                            <li><a href="#">Delete</a></li>
                            <li><a href="#">Save</a></li>
                            <li><a href="#">Revert</a></li>
                            <li class="divider"></li>
                            <li><a href="#">Export to file...</a></li>
                            <li><a href="#">Import from file...</a></li>
                        </ul>
                    </li>
                    <li class="dropdown" id="menu_users">
                        <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_users">Users
                            <b class="caret"></b></a>
                        <ul class="dropdown-menu">
                            <li><a href="#">Show user console...</a></li>
                        </ul>
                    </li>
                    <li class="dropdown" id="menu_config">
                        <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_config">Config
                            <b class="caret"></b></a>
                        <ul class="dropdown-menu">
                            <li><a href="#">Server</a></li>
                            <li><a href="#">Agent runner</a></li>
                            <li><a href="#">World runner</a></li>
                        </ul>
                    </li>
                    <li class="dropdown" id="menu_help">
                        <a class="dropdown-toggle" data-toggle="dropdown" href="#menu_help">Help
                            <b class="caret"></b></a>
                        <ul class="dropdown-menu">
                            <li><a href="#">About</a></li>
                            <li><a href="#">Documentation</a></li>
                            <li class="divider"></li>
                            <li><a href="#">Contact</a></li>
                        </ul>
                    </li>
                </ul>
            </div>
            <!--/.nav-collapse -->
        </div>
    </div>
</div>

<div class="container-fluid">
    <div class="row-fluid">
        <div class="span2">
            <div class="well sidebar-nav">
                <ul class="nav nav-list">
                    <li class="nav-header">My Agents</li>
                    <li class="active"><a href="#">Agent1</a></li>
                    <li><a href="#">Agent2</a></li>
                    <li><a href="#">Agent3</a></li>
                    <li><a href="#">Agent4</a></li>
                    <li class="nav-header">Other Agents</li>
                    <li><a href="#">Agent10</a></li>
                    <li><a href="#">Agent11</a></li>
                    <li class="nav-header">Active World</li>
                    <li><a href="#">Object1</a></li>
                    <li><a href="#">Object2</a></li>
                    <li><a href="#">Object3</a></li>
                </ul>
            </div>
            <!--/.well -->
        </div>
        <!--/span-->
        <div class="span10">
            <div class="sectionbar">
                <form class="navbar-form">
                    <table>
                        <tr>
                            <td><span data-toggle="collapse" data-target="#nodenet_editor, #nodespace_control"><i
                                    class="icon-chevron-right"></i></span></td>


                            <td><input class="span3" disabled="disabled" value="Agent1"/></td>

                            <td><span class="btn-group">
                          <button class="btn"><i class="icon-fast-backward"></i></button>
                          <button class="btn"><i class="icon-play"></i></button>
                          <button class="btn"><i class="icon-step-forward"></i></button>
                          <button class="btn"><i class="icon-pause"></i></button>
                    </span></td>

                            <td><input class="span1" disabled="disabled" style="text-align:right" value="0"/></td>
                            <td><div id="nodespace_control" class="collapse in">
                                &nbsp;Nodespace:
                                <input class="span3" disabled="disabled" value="Root"/>
                                <button class="btn"><i class="icon-share"></i></button>
                            </div>

                            </td>
                        </tr>
                    </table>

                </form>
            </div>


            <div id="nodenet_editor" class="collapse in">
                <div style="overflow:scroll; height:400px">
                    <canvas id="nodenet" width="700" height="500" style="background:#eeeeee"></canvas>
                </div>
            </div>
            <div class="sectionbar">
                <form class="navbar-form">
                    <table>
                        <tr>
                            <td><span data-toggle="collapse" data-target="#monitor, #monitor_controls"><i
                                    class="icon-chevron-right"></i></span></td>


                            <td> Nodenet Monitor &nbsp;</td>

                            <td><div class="collapse" id="monitor_controls">
                          <button class="btn">Clear</button>
                    </div></td>

                        </tr>
                    </table>

                </form>
            </div>


            <div id="monitor" class="collapse">
                <div class="hero-unit">
                    <p>Monitor plugin for individual activities</p>
                </div>
            </div>
            <div class="sectionbar">
                <form class="navbar-form">
                    <table>
                        <tr>
                            <td><span data-toggle="collapse" data-target="#world_editor"><i
                                    class="icon-chevron-right"></i></span></td>


                            <td><input class="span3" disabled="disabled" value="World"/></td>

                            <td><span class="btn-group">
                          <button class="btn"><i class="icon-fast-backward"></i></button>
                          <button class="btn"><i class="icon-play"></i></button>
                          <button class="btn"><i class="icon-step-forward"></i></button>
                          <button class="btn"><i class="icon-pause"></i></button>
                    </span></td>

                            <td><input class="span1" disabled="disabled" style="text-align:right" value="0"/></td>
                        </tr>
                    </table>

                </form>
            </div>


            <div id="world_editor" class="collapse">
                <div class="hero-unit">
                    <p>World Viewer Placeholder</p>
                </div>
            </div>


            <!--/span-->
        </div>
        <!--/row-->
    </div>
    <!--/span-->
</div>
<!--/row-->


</div><!--/.fluid-container-->

<script src="static/js/jquery.min.js" type="text/javascript"></script>
<script src="static/js/bootstrap.min.js" type="text/javascript"></script>
<script src="static/js/micropsiviewer.js" type="text/javascript"></script>
<script src="static/js/paper.js" type="text/javascript"></script>
<script src="static/js/nodenet.js" type="text/paperscript" canvas="nodenet"></script>

</body>
</html>